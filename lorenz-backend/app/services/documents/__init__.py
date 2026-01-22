"""
LORENZ SaaS - Document Processing Service
==========================================

Multi-format document processing for RAG indexing:
- PDF (native + OCR)
- DOCX, DOC
- TXT, MD, HTML
- Excel (XLSX, CSV)
- Images with OCR
"""

from .processor import (
    DocumentProcessor,
    DocumentChunk,
    ProcessingResult,
    ProcessingStatus,
    ChunkingStrategy,
    get_document_processor,
)

__all__ = [
    "DocumentProcessor",
    "DocumentChunk",
    "ProcessingResult",
    "ProcessingStatus",
    "ChunkingStrategy",
    "get_document_processor",
]
