"""
LORENZ SaaS - Advanced RAG Service
===================================

Production-grade Retrieval-Augmented Generation adapted from lorenz_rag_system.py
for multi-tenant SaaS deployment.

Features:
- Hybrid Search (Vector + BM25)
- Reciprocal Rank Fusion (RRF)
- Cross-encoder Reranking
- Multi-tenant collection isolation
- Async/await support for FastAPI
"""

import os
import logging
import hashlib
from typing import List, Dict, Tuple, Optional, Any
from datetime import datetime
from uuid import UUID
import asyncio
from concurrent.futures import ThreadPoolExecutor

import numpy as np
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models import RAGDocument
from app.config import settings

logger = logging.getLogger(__name__)

# Thread pool for CPU-bound operations (embeddings, BM25)
_executor = ThreadPoolExecutor(max_workers=4)


# ============================================================================
# CONFIGURATION
# ============================================================================

# Embedding Model (multilingual, 768 dims)
EMBEDDING_MODEL = os.getenv(
    'RAG_EMBEDDING_MODEL',
    'sentence-transformers/paraphrase-multilingual-mpnet-base-v2'
)

# Reranker Model
RERANKER_MODEL = os.getenv(
    'RAG_RERANKER_MODEL',
    'BAAI/bge-reranker-base'
)

# Search parameters
DEFAULT_TOP_K = 5
FUSION_K = 60  # RRF constant
MAX_CANDIDATES = 20  # Candidates before reranking


# ============================================================================
# LAZY LOADING SINGLETONS
# ============================================================================

_encoder = None
_reranker = None
_qdrant_client = None


def get_encoder():
    """Lazy load sentence transformer encoder"""
    global _encoder
    if _encoder is None:
        try:
            from sentence_transformers import SentenceTransformer
            logger.info(f"Loading embedding model: {EMBEDDING_MODEL}")
            _encoder = SentenceTransformer(EMBEDDING_MODEL)
            logger.info(f"Embedding model loaded (dim={_encoder.get_sentence_embedding_dimension()})")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            return None
    return _encoder


def get_reranker():
    """Lazy load cross-encoder reranker"""
    global _reranker
    if _reranker is None:
        try:
            from FlagEmbedding import FlagReranker
            logger.info(f"Loading reranker: {RERANKER_MODEL}")
            _reranker = FlagReranker(RERANKER_MODEL, use_fp16=True)
            logger.info("Reranker loaded")
        except ImportError:
            logger.warning("FlagEmbedding not available, reranking disabled")
            return None
        except Exception as e:
            logger.error(f"Failed to load reranker: {e}")
            return None
    return _reranker


def get_qdrant_client():
    """Get Qdrant client singleton"""
    global _qdrant_client
    if _qdrant_client is None:
        try:
            from qdrant_client import QdrantClient
            _qdrant_client = QdrantClient(
                host=settings.QDRANT_HOST,
                port=settings.QDRANT_PORT,
                api_key=settings.QDRANT_API_KEY or None
            )
            logger.info(f"Qdrant client connected to {settings.QDRANT_HOST}:{settings.QDRANT_PORT}")
        except Exception as e:
            logger.error(f"Failed to connect to Qdrant: {e}")
            return None
    return _qdrant_client


# ============================================================================
# ADVANCED RAG SERVICE
# ============================================================================

class AdvancedRAGService:
    """
    Multi-tenant Advanced RAG Service

    Pipeline:
    1. Query → Embedding (async)
    2. Parallel Search:
       - Vector Search (Qdrant - semantic)
       - BM25 Search (PostgreSQL - keyword)
    3. Fusion: Reciprocal Rank Fusion (RRF)
    4. Reranking: Cross-encoder reranker
    5. Return: Top-K most relevant documents
    """

    def __init__(self, db: AsyncSession, tenant_id: UUID, user_id: UUID):
        self.db = db
        self.tenant_id = tenant_id
        self.user_id = user_id
        self.collection_name = f"tenant_{tenant_id}"

        # BM25 cache (per request)
        self._bm25_index = None
        self._bm25_corpus = []
        self._bm25_ids = []

    def _get_collection_name(self) -> str:
        """Get tenant-specific Qdrant collection name"""
        return f"tenant_{self.tenant_id}"

    async def _ensure_collection(self):
        """Ensure Qdrant collection exists for tenant"""
        qdrant = get_qdrant_client()
        if not qdrant:
            return False

        encoder = get_encoder()
        if not encoder:
            return False

        try:
            from qdrant_client.models import Distance, VectorParams

            collection_name = self._get_collection_name()
            collections = qdrant.get_collections().collections
            collection_names = [c.name for c in collections]

            if collection_name not in collection_names:
                embedding_dim = encoder.get_sentence_embedding_dimension()
                qdrant.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(
                        size=embedding_dim,
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"Created Qdrant collection: {collection_name}")

            return True
        except Exception as e:
            logger.error(f"Failed to ensure collection: {e}")
            return False

    async def _encode_async(self, text: str) -> Optional[np.ndarray]:
        """Encode text to embedding vector (async wrapper)"""
        encoder = get_encoder()
        if not encoder:
            return None

        loop = asyncio.get_event_loop()
        embedding = await loop.run_in_executor(
            _executor,
            lambda: encoder.encode(text, convert_to_numpy=True)
        )
        return embedding

    async def _encode_batch_async(self, texts: List[str]) -> Optional[np.ndarray]:
        """Encode batch of texts (async wrapper)"""
        encoder = get_encoder()
        if not encoder:
            return None

        loop = asyncio.get_event_loop()
        embeddings = await loop.run_in_executor(
            _executor,
            lambda: encoder.encode(texts, convert_to_numpy=True)
        )
        return embeddings

    async def vector_search(
        self,
        query: str,
        top_k: int = MAX_CANDIDATES,
        source_types: Optional[List[str]] = None
    ) -> List[Dict]:
        """
        Semantic vector search via Qdrant

        Args:
            query: Search query
            top_k: Number of results
            source_types: Filter by source types

        Returns:
            List of document dicts with scores
        """
        qdrant = get_qdrant_client()
        if not qdrant:
            return []

        try:
            # Encode query
            query_vector = await self._encode_async(query)
            if query_vector is None:
                return []

            # Build filter
            from qdrant_client.models import Filter, FieldCondition, MatchValue, MatchAny

            must_conditions = [
                FieldCondition(
                    key="user_id",
                    match=MatchValue(value=str(self.user_id))
                )
            ]

            if source_types:
                must_conditions.append(
                    FieldCondition(
                        key="source_type",
                        match=MatchAny(any=source_types)
                    )
                )

            # Search
            results = qdrant.search(
                collection_name=self._get_collection_name(),
                query_vector=query_vector.tolist(),
                limit=top_k,
                query_filter=Filter(must=must_conditions) if must_conditions else None
            )

            # Format results
            documents = []
            for rank, hit in enumerate(results):
                documents.append({
                    "doc_id": str(hit.id),
                    "content": hit.payload.get("content", ""),
                    "title": hit.payload.get("title", ""),
                    "score": hit.score,
                    "rank": rank + 1,
                    "source": "vector",
                    "metadata": hit.payload.get("metadata", {})
                })

            return documents

        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            return []

    async def bm25_search(
        self,
        query: str,
        top_k: int = MAX_CANDIDATES,
        source_types: Optional[List[str]] = None
    ) -> List[Dict]:
        """
        Keyword-based BM25 search via PostgreSQL

        Args:
            query: Search query
            top_k: Number of results
            source_types: Filter by source types

        Returns:
            List of document dicts with scores
        """
        try:
            from rank_bm25 import BM25Okapi

            # Fetch documents from database
            db_query = select(RAGDocument).where(
                RAGDocument.user_id == self.user_id,
                RAGDocument.status == "indexed"
            )

            if source_types:
                db_query = db_query.where(RAGDocument.source_type.in_(source_types))

            result = await self.db.execute(db_query)
            documents = result.scalars().all()

            if not documents:
                return []

            # Build BM25 index
            corpus = [doc.content for doc in documents]
            doc_ids = [str(doc.id) for doc in documents]

            # Tokenize
            tokenized_corpus = [doc.lower().split() for doc in corpus]
            bm25 = BM25Okapi(tokenized_corpus)

            # Search
            tokenized_query = query.lower().split()
            scores = bm25.get_scores(tokenized_query)

            # Get top-k
            top_indices = np.argsort(scores)[::-1][:top_k]

            # Format results
            results = []
            for rank, idx in enumerate(top_indices):
                if scores[idx] > 0:
                    doc = documents[idx]
                    results.append({
                        "doc_id": doc_ids[idx],
                        "content": corpus[idx],
                        "title": doc.title,
                        "score": float(scores[idx]),
                        "rank": rank + 1,
                        "source": "bm25",
                        "metadata": doc.metadata or {}
                    })

            return results

        except ImportError:
            logger.warning("rank_bm25 not installed, BM25 search disabled")
            return []
        except Exception as e:
            logger.error(f"BM25 search failed: {e}")
            return []

    def reciprocal_rank_fusion(
        self,
        vector_results: List[Dict],
        bm25_results: List[Dict],
        k: int = FUSION_K
    ) -> List[Dict]:
        """
        Reciprocal Rank Fusion (RRF) for combining search results

        RRF Score = sum(1 / (k + rank)) for each result list

        Args:
            vector_results: Results from vector search
            bm25_results: Results from BM25 search
            k: RRF constant (default 60)

        Returns:
            Fused and ranked results
        """
        # Collect all doc_ids
        all_doc_ids = set()
        for doc in vector_results + bm25_results:
            all_doc_ids.add(doc["doc_id"])

        # Calculate RRF scores
        rrf_scores = {}
        doc_contents = {}
        doc_titles = {}
        doc_metadata = {}

        for doc_id in all_doc_ids:
            score = 0.0

            # Vector contribution
            for doc in vector_results:
                if doc["doc_id"] == doc_id:
                    score += 1.0 / (k + doc["rank"])
                    doc_contents[doc_id] = doc["content"]
                    doc_titles[doc_id] = doc.get("title", "")
                    doc_metadata[doc_id] = doc.get("metadata", {})
                    break

            # BM25 contribution
            for doc in bm25_results:
                if doc["doc_id"] == doc_id:
                    score += 1.0 / (k + doc["rank"])
                    if doc_id not in doc_contents:
                        doc_contents[doc_id] = doc["content"]
                        doc_titles[doc_id] = doc.get("title", "")
                        doc_metadata[doc_id] = doc.get("metadata", {})
                    break

            rrf_scores[doc_id] = score

        # Sort by RRF score
        sorted_docs = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)

        # Format output
        fused_results = []
        for rank, (doc_id, score) in enumerate(sorted_docs):
            fused_results.append({
                "doc_id": doc_id,
                "content": doc_contents.get(doc_id, ""),
                "title": doc_titles.get(doc_id, ""),
                "rrf_score": score,
                "rank": rank + 1,
                "metadata": doc_metadata.get(doc_id, {})
            })

        return fused_results

    async def rerank(
        self,
        query: str,
        documents: List[Dict],
        top_k: int = DEFAULT_TOP_K
    ) -> List[Dict]:
        """
        Rerank documents using cross-encoder

        Args:
            query: User query
            documents: List of candidate documents
            top_k: Number of top results to return

        Returns:
            Reranked top-k documents
        """
        reranker = get_reranker()

        if not reranker or not documents:
            # Return top-k by current score if no reranker
            return documents[:top_k]

        try:
            # Prepare pairs for reranking
            pairs = [[query, doc["content"]] for doc in documents]

            # Compute reranking scores (CPU-bound, run in executor)
            loop = asyncio.get_event_loop()
            rerank_scores = await loop.run_in_executor(
                _executor,
                lambda: reranker.compute_score(pairs, normalize=True)
            )

            # Handle single result
            if isinstance(rerank_scores, float):
                rerank_scores = [rerank_scores]

            # Add rerank scores to documents
            for doc, score in zip(documents, rerank_scores):
                doc["rerank_score"] = float(score)

            # Sort by rerank score
            reranked = sorted(
                documents,
                key=lambda x: x.get("rerank_score", 0),
                reverse=True
            )

            return reranked[:top_k]

        except Exception as e:
            logger.error(f"Reranking failed: {e}")
            return documents[:top_k]

    async def hybrid_search(
        self,
        query: str,
        top_k: int = DEFAULT_TOP_K,
        source_types: Optional[List[str]] = None,
        use_reranking: bool = True
    ) -> List[Dict]:
        """
        Complete hybrid search pipeline

        Args:
            query: User query
            top_k: Number of final results
            source_types: Filter by source types
            use_reranking: Whether to use reranking

        Returns:
            Top-k most relevant documents
        """
        logger.info(f"Hybrid search: '{query[:50]}...'")

        # Step 1: Parallel search
        vector_task = self.vector_search(query, MAX_CANDIDATES, source_types)
        bm25_task = self.bm25_search(query, MAX_CANDIDATES, source_types)

        vector_results, bm25_results = await asyncio.gather(vector_task, bm25_task)

        logger.debug(f"Vector: {len(vector_results)} results, BM25: {len(bm25_results)} results")

        # Step 2: Fusion
        fused_results = self.reciprocal_rank_fusion(vector_results, bm25_results)

        logger.debug(f"Fused: {len(fused_results)} results")

        # Step 3: Reranking
        if use_reranking and get_reranker():
            final_results = await self.rerank(query, fused_results[:MAX_CANDIDATES], top_k)
            logger.info(f"Reranked to top-{top_k}")
        else:
            final_results = fused_results[:top_k]
            logger.info(f"Returned top-{top_k} (no reranking)")

        return final_results

    async def build_context(
        self,
        query: str,
        max_tokens: int = 2000,
        source_types: Optional[List[str]] = None
    ) -> str:
        """
        Build context from relevant documents for LLM

        Args:
            query: User query
            max_tokens: Maximum context tokens (approx)
            source_types: Filter by source types

        Returns:
            Formatted context string
        """
        # Search for relevant documents
        results = await self.hybrid_search(query, top_k=5, source_types=source_types)

        if not results:
            return ""

        # Build context
        context_parts = []
        total_chars = 0
        max_chars = max_tokens * 4  # Rough estimate: 1 token ≈ 4 chars

        for idx, doc in enumerate(results, 1):
            content = doc["content"]
            title = doc.get("title", f"Document {idx}")

            # Check token limit
            if total_chars + len(content) > max_chars:
                # Truncate last document
                remaining = max_chars - total_chars
                if remaining > 100:
                    context_parts.append(f"[{idx}] {title}:\n{content[:remaining]}...")
                break

            context_parts.append(f"[{idx}] {title}:\n{content}")
            total_chars += len(content)

        context = "\n\n".join(context_parts)

        logger.info(f"Built context: {total_chars} chars from {len(context_parts)} docs")

        return context

    async def index_document(
        self,
        title: str,
        content: str,
        source_type: str = "file",
        metadata: Optional[Dict] = None
    ) -> Optional[str]:
        """
        Index a document into the RAG system

        Args:
            title: Document title
            content: Document content
            source_type: Type of source (file, email, note, etc.)
            metadata: Additional metadata

        Returns:
            Document ID or None on failure
        """
        await self._ensure_collection()

        try:
            # Compute content hash for deduplication
            content_hash = hashlib.sha256(content.encode()).hexdigest()

            # Check for duplicate
            query = select(RAGDocument).where(
                RAGDocument.user_id == self.user_id,
                RAGDocument.content_hash == content_hash
            )
            result = await self.db.execute(query)
            existing = result.scalar_one_or_none()

            if existing:
                logger.info(f"Document already indexed: {title}")
                return str(existing.id)

            # Create database record
            doc = RAGDocument(
                user_id=self.user_id,
                source_type=source_type,
                title=title,
                content=content,
                content_hash=content_hash,
                chunk_index=0,
                total_chunks=1,
                metadata=metadata or {},
                status="indexing"
            )
            self.db.add(doc)
            await self.db.flush()

            # Generate and store embedding in Qdrant
            qdrant = get_qdrant_client()
            if qdrant:
                embedding = await self._encode_async(content)
                if embedding is not None:
                    from qdrant_client.models import PointStruct

                    qdrant.upsert(
                        collection_name=self._get_collection_name(),
                        points=[
                            PointStruct(
                                id=str(doc.id),
                                vector=embedding.tolist(),
                                payload={
                                    "user_id": str(self.user_id),
                                    "source_type": source_type,
                                    "title": title,
                                    "content": content[:1000],  # Store snippet
                                    "metadata": metadata or {}
                                }
                            )
                        ]
                    )

                    doc.qdrant_point_id = str(doc.id)

            doc.status = "indexed"
            self.db.add(doc)
            await self.db.commit()

            logger.info(f"Indexed document: {title}")
            return str(doc.id)

        except Exception as e:
            logger.error(f"Failed to index document: {e}")
            return None

    async def delete_document(self, document_id: UUID) -> bool:
        """Delete a document from the RAG system"""
        try:
            query = select(RAGDocument).where(
                RAGDocument.id == document_id,
                RAGDocument.user_id == self.user_id
            )
            result = await self.db.execute(query)
            doc = result.scalar_one_or_none()

            if not doc:
                return False

            # Remove from Qdrant
            qdrant = get_qdrant_client()
            if qdrant and doc.qdrant_point_id:
                try:
                    qdrant.delete(
                        collection_name=self._get_collection_name(),
                        points_selector=[doc.qdrant_point_id]
                    )
                except Exception as e:
                    logger.warning(f"Failed to delete from Qdrant: {e}")

            await self.db.delete(doc)
            await self.db.commit()

            return True

        except Exception as e:
            logger.error(f"Failed to delete document: {e}")
            return False

    async def get_stats(self) -> Dict:
        """Get RAG statistics for this user"""
        try:
            # Count documents
            count_query = select(func.count(RAGDocument.id)).where(
                RAGDocument.user_id == self.user_id
            )
            result = await self.db.execute(count_query)
            total_docs = result.scalar()

            # Count by source type
            source_query = select(
                RAGDocument.source_type,
                func.count(RAGDocument.id)
            ).where(
                RAGDocument.user_id == self.user_id
            ).group_by(RAGDocument.source_type)

            result = await self.db.execute(source_query)
            sources = {row[0]: row[1] for row in result.all()}

            # Qdrant stats
            qdrant = get_qdrant_client()
            vector_count = 0
            if qdrant:
                try:
                    info = qdrant.get_collection(self._get_collection_name())
                    vector_count = info.points_count
                except:
                    pass

            return {
                "total_documents": total_docs,
                "vector_indexed": vector_count,
                "sources": sources,
                "embedding_model": EMBEDDING_MODEL,
                "reranker_enabled": get_reranker() is not None
            }

        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {}


# ============================================================================
# FACTORY FUNCTION
# ============================================================================

def create_advanced_rag(
    db: AsyncSession,
    tenant_id: UUID,
    user_id: UUID
) -> AdvancedRAGService:
    """
    Factory function to create an Advanced RAG service instance

    Args:
        db: Database session
        tenant_id: Tenant UUID for collection isolation
        user_id: User UUID for document ownership

    Returns:
        Configured AdvancedRAGService instance
    """
    return AdvancedRAGService(db, tenant_id, user_id)
