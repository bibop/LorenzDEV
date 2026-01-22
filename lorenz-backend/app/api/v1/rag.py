"""
LORENZ SaaS - RAG (Knowledge Base) Routes
==========================================

Advanced document upload, indexing, and search API.
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, BackgroundTasks, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime
import logging
import hashlib

from app.database import get_db
from app.services.rag import RAGService
from app.services.rag.advanced import AdvancedRAGService, create_advanced_rag
from app.services.documents import (
    DocumentProcessor,
    get_document_processor,
    ProcessingStatus,
    ChunkingStrategy
)
from app.api.deps import get_current_user
from app.models import User, RAGDocument

router = APIRouter()
logger = logging.getLogger(__name__)


# ============================================================================
# SCHEMAS
# ============================================================================

class SearchRequest(BaseModel):
    """Search request"""
    query: str = Field(..., min_length=1)
    source_types: Optional[List[str]] = None
    limit: int = Field(default=10, ge=1, le=50)
    use_reranking: bool = True


class SearchResult(BaseModel):
    """Search result item"""
    doc_id: str
    title: str
    content: str
    score: float
    source: str
    metadata: Dict[str, Any] = {}


class SearchResponse(BaseModel):
    """Search response"""
    results: List[SearchResult]
    total: int
    query: str


class DocumentResponse(BaseModel):
    """Document info response"""
    id: str
    title: str
    source_type: str
    status: str
    chunk_count: int
    metadata: Dict[str, Any]
    created_at: datetime


class UploadResponse(BaseModel):
    """Upload response"""
    document_id: str
    filename: str
    status: str
    message: str


class BatchUploadResponse(BaseModel):
    """Batch upload response"""
    uploaded: int
    failed: int
    documents: List[UploadResponse]


class IndexingStatusResponse(BaseModel):
    """Indexing status response"""
    document_id: str
    filename: str
    status: str
    progress: float
    chunks_indexed: int
    error: Optional[str] = None


class RAGStatsResponse(BaseModel):
    """RAG statistics"""
    total_documents: int
    total_chunks: int
    sources: Dict[str, int]
    vector_indexed: int
    embedding_model: str
    reranker_enabled: bool


# ============================================================================
# SUPPORTED FILE TYPES
# ============================================================================

ALLOWED_CONTENT_TYPES = [
    # Text
    "text/plain",
    "text/markdown",
    "text/html",
    "text/csv",
    # PDF
    "application/pdf",
    # Microsoft Office
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    # OpenDocument
    "application/vnd.oasis.opendocument.text",
    # Images (for OCR)
    "image/png",
    "image/jpeg",
    "image/tiff",
    # Rich Text
    "application/rtf",
]

ALLOWED_EXTENSIONS = [
    ".txt", ".md", ".markdown", ".html", ".htm", ".csv",
    ".pdf",
    ".docx", ".doc", ".xlsx", ".xls", ".pptx",
    ".odt",
    ".png", ".jpg", ".jpeg", ".tiff", ".tif",
    ".rtf"
]

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

async def index_document_task(
    user_id: UUID,
    tenant_id: UUID,
    content: bytes,
    filename: str,
    content_type: str,
    db: AsyncSession
):
    """Background task to process and index a document"""
    try:
        # Create document processor
        processor = get_document_processor(
            chunk_size=1000,
            chunk_overlap=200,
            chunking_strategy=ChunkingStrategy.RECURSIVE,
            enable_ocr=True
        )

        # Process document
        result = await processor.process_document(
            content=content,
            filename=filename,
            content_type=content_type
        )

        if result.status == ProcessingStatus.FAILED:
            logger.error(f"Document processing failed: {result.error}")
            return

        # Create Advanced RAG service for indexing
        rag = create_advanced_rag(db, tenant_id, user_id)

        # Index each chunk
        for chunk in result.chunks:
            await rag.index_document(
                title=f"{filename} (chunk {chunk.chunk_index + 1}/{chunk.total_chunks})",
                content=chunk.content,
                source_type="file",
                metadata={
                    "filename": filename,
                    "content_type": content_type,
                    "content_hash": result.content_hash,
                    "chunk_index": chunk.chunk_index,
                    "total_chunks": chunk.total_chunks,
                    **result.metadata
                }
            )

        logger.info(f"Indexed {filename}: {len(result.chunks)} chunks")

    except Exception as e:
        logger.error(f"Indexing failed for {filename}: {e}", exc_info=True)


# ============================================================================
# SEARCH ENDPOINTS
# ============================================================================

@router.post("/search", response_model=SearchResponse)
async def search_knowledge_base(
    request: SearchRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Search the user's knowledge base using hybrid search.

    Uses advanced RAG pipeline:
    1. Vector search (semantic similarity)
    2. BM25 search (keyword matching)
    3. Reciprocal Rank Fusion
    4. Cross-encoder reranking (optional)
    """
    try:
        rag = create_advanced_rag(db, current_user.tenant_id, current_user.id)

        results = await rag.hybrid_search(
            query=request.query,
            top_k=request.limit,
            source_types=request.source_types,
            use_reranking=request.use_reranking
        )

        return SearchResponse(
            results=[
                SearchResult(
                    doc_id=r.get("doc_id", ""),
                    title=r.get("title", ""),
                    content=r.get("content", "")[:500],  # Truncate for response
                    score=r.get("rerank_score", r.get("rrf_score", r.get("score", 0))),
                    source=r.get("source", "hybrid"),
                    metadata=r.get("metadata", {})
                )
                for r in results
            ],
            total=len(results),
            query=request.query
        )

    except Exception as e:
        logger.error(f"Search failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Search failed")


@router.get("/search/simple")
async def simple_search(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Simple search endpoint (GET method for easy testing)
    """
    rag = RAGService(db)
    results = await rag.search(
        user_id=current_user.id,
        tenant_id=current_user.tenant_id,
        query=q,
        limit=limit
    )
    return {"results": results, "total": len(results), "query": q}


@router.post("/context")
async def get_context_for_query(
    query: str,
    max_tokens: int = 2000,
    source_types: Optional[List[str]] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get formatted context for a query (used by Twin service)
    """
    rag = create_advanced_rag(db, current_user.tenant_id, current_user.id)

    context = await rag.build_context(
        query=query,
        max_tokens=max_tokens,
        source_types=source_types
    )

    return {
        "context": context,
        "query": query,
        "char_count": len(context)
    }


# ============================================================================
# DOCUMENT MANAGEMENT ENDPOINTS
# ============================================================================

@router.get("/documents", response_model=Dict[str, Any])
async def list_documents(
    source_type: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List indexed documents in the knowledge base.
    """
    rag_service = RAGService(db)
    documents, total = await rag_service.list_documents(
        user_id=current_user.id,
        source_type=source_type,
        limit=limit,
        offset=offset
    )

    return {
        "documents": documents,
        "total": total,
        "limit": limit,
        "offset": offset,
        "has_more": offset + len(documents) < total
    }


@router.get("/documents/{document_id}")
async def get_document(
    document_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific document"""
    from sqlalchemy import select

    query = select(RAGDocument).where(
        RAGDocument.id == document_id,
        RAGDocument.user_id == current_user.id
    )
    result = await db.execute(query)
    doc = result.scalar_one_or_none()

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    return {
        "id": str(doc.id),
        "title": doc.title,
        "content": doc.content,
        "source_type": doc.source_type,
        "status": doc.status,
        "chunk_index": doc.chunk_index,
        "total_chunks": doc.total_chunks,
        "metadata": doc.metadata,
        "created_at": doc.created_at
    }


# ============================================================================
# UPLOAD ENDPOINTS
# ============================================================================

@router.post("/documents/upload", response_model=UploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload and index a single document.

    Supported formats:
    - PDF, DOCX, DOC, TXT, MD, HTML
    - XLSX, XLS, CSV
    - PPTX, ODT
    - Images (PNG, JPG, TIFF) - with OCR
    """
    # Check file extension
    filename = file.filename or "unknown"
    ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {ext}. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # Read content
    content = await file.read()

    # Check file size
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size: {MAX_FILE_SIZE // (1024*1024)}MB"
        )

    # Generate document ID
    document_id = hashlib.sha256(
        f"{current_user.id}:{filename}:{len(content)}".encode()
    ).hexdigest()[:16]

    # Queue for background processing
    background_tasks.add_task(
        index_document_task,
        user_id=current_user.id,
        tenant_id=current_user.tenant_id,
        content=content,
        filename=filename,
        content_type=file.content_type or "application/octet-stream",
        db=db
    )

    return UploadResponse(
        document_id=document_id,
        filename=filename,
        status="processing",
        message="Document uploaded and indexing started"
    )


@router.post("/documents/upload/batch", response_model=BatchUploadResponse)
async def upload_documents_batch(
    files: List[UploadFile] = File(...),
    background_tasks: BackgroundTasks = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload multiple documents at once (max 10 files).
    """
    if len(files) > 10:
        raise HTTPException(
            status_code=400,
            detail="Maximum 10 files per batch upload"
        )

    results = []
    uploaded = 0
    failed = 0

    for file in files:
        filename = file.filename or "unknown"
        ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

        if ext not in ALLOWED_EXTENSIONS:
            results.append(UploadResponse(
                document_id="",
                filename=filename,
                status="failed",
                message=f"Unsupported file type: {ext}"
            ))
            failed += 1
            continue

        try:
            content = await file.read()

            if len(content) > MAX_FILE_SIZE:
                results.append(UploadResponse(
                    document_id="",
                    filename=filename,
                    status="failed",
                    message="File too large"
                ))
                failed += 1
                continue

            document_id = hashlib.sha256(
                f"{current_user.id}:{filename}:{len(content)}".encode()
            ).hexdigest()[:16]

            background_tasks.add_task(
                index_document_task,
                user_id=current_user.id,
                tenant_id=current_user.tenant_id,
                content=content,
                filename=filename,
                content_type=file.content_type or "application/octet-stream",
                db=db
            )

            results.append(UploadResponse(
                document_id=document_id,
                filename=filename,
                status="processing",
                message="Indexing started"
            ))
            uploaded += 1

        except Exception as e:
            logger.error(f"Upload failed for {filename}: {e}")
            results.append(UploadResponse(
                document_id="",
                filename=filename,
                status="failed",
                message=str(e)
            ))
            failed += 1

    return BatchUploadResponse(
        uploaded=uploaded,
        failed=failed,
        documents=results
    )


@router.post("/documents/index-text")
async def index_text_directly(
    title: str,
    content: str,
    source_type: str = "note",
    metadata: Optional[Dict[str, Any]] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Index text content directly without file upload.

    Useful for:
    - Notes
    - Copied text
    - API-generated content
    """
    if len(content) < 10:
        raise HTTPException(
            status_code=400,
            detail="Content too short (minimum 10 characters)"
        )

    rag = create_advanced_rag(db, current_user.tenant_id, current_user.id)

    doc_id = await rag.index_document(
        title=title,
        content=content,
        source_type=source_type,
        metadata=metadata or {}
    )

    if not doc_id:
        raise HTTPException(
            status_code=500,
            detail="Failed to index content"
        )

    return {
        "document_id": doc_id,
        "title": title,
        "status": "indexed",
        "content_length": len(content)
    }


# ============================================================================
# DELETE AND REINDEX
# ============================================================================

@router.delete("/documents/{document_id}")
async def delete_document(
    document_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a document from the knowledge base.
    """
    rag = create_advanced_rag(db, current_user.tenant_id, current_user.id)

    success = await rag.delete_document(document_id)

    if not success:
        raise HTTPException(status_code=404, detail="Document not found")

    return {"message": "Document deleted", "document_id": str(document_id)}


@router.post("/reindex")
async def reindex_all(
    source_type: Optional[str] = None,
    background_tasks: BackgroundTasks = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Trigger full reindex of user's content.
    """
    rag_service = RAGService(db)

    background_tasks.add_task(
        rag_service.reindex_user_content,
        user_id=current_user.id,
        tenant_id=current_user.tenant_id,
        source_type=source_type
    )

    return {
        "message": "Reindex started",
        "source_type": source_type or "all"
    }


# ============================================================================
# STATISTICS AND SOURCES
# ============================================================================

@router.get("/sources")
async def get_indexed_sources(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get summary of indexed sources.
    """
    rag_service = RAGService(db)
    sources = await rag_service.get_source_summary(current_user.id)
    return {"sources": sources}


@router.get("/stats", response_model=RAGStatsResponse)
async def get_rag_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get comprehensive RAG statistics.
    """
    rag = create_advanced_rag(db, current_user.tenant_id, current_user.id)
    stats = await rag.get_stats()

    return RAGStatsResponse(
        total_documents=stats.get("total_documents", 0),
        total_chunks=stats.get("total_documents", 0),  # Adjust based on actual chunk count
        sources=stats.get("sources", {}),
        vector_indexed=stats.get("vector_indexed", 0),
        embedding_model=stats.get("embedding_model", "unknown"),
        reranker_enabled=stats.get("reranker_enabled", False)
    )


# ============================================================================
# SUPPORTED FORMATS INFO
# ============================================================================

@router.get("/formats")
async def get_supported_formats():
    """
    Get list of supported file formats for upload.
    """
    return {
        "extensions": ALLOWED_EXTENSIONS,
        "content_types": ALLOWED_CONTENT_TYPES,
        "max_file_size_mb": MAX_FILE_SIZE // (1024 * 1024),
        "max_batch_files": 10,
        "features": {
            "pdf_ocr": True,
            "image_ocr": True,
            "office_documents": True,
            "spreadsheets": True,
            "presentations": True
        }
    }
