"""
LORENZ SaaS - RAG Document Model
"""

from sqlalchemy import Column, String, ForeignKey, Text, Integer, Float
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid

from app.models.base import Base, TimestampMixin


class RAGDocument(Base, TimestampMixin):
    """
    RAG Document model - stores indexed documents for retrieval.
    Actual embeddings are stored in Qdrant, this is metadata.
    """
    __tablename__ = "rag_documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Source type and ID
    source_type = Column(String(50), nullable=False, index=True)
    # Source types: email, calendar, file, social, conversation, manual
    source_id = Column(String(255), nullable=True, index=True)  # Original ID from source

    # Document info
    title = Column(String(500), nullable=True)
    content = Column(Text, nullable=True)  # Original text content
    content_hash = Column(String(64), nullable=True, index=True)  # SHA256 for deduplication

    # Chunking info
    chunk_index = Column(Integer, default=0)  # If document was split into chunks
    total_chunks = Column(Integer, default=1)
    parent_document_id = Column(UUID(as_uuid=True), nullable=True)  # Link to parent if chunked

    # Qdrant reference
    qdrant_point_id = Column(String(255), nullable=True, index=True)
    embedding_model = Column(String(100), default="all-MiniLM-L6-v2")

    # Document metadata
    document_metadata = Column(JSONB, default=dict)
    # Example for email:
    # {
    #     "from": "sender@example.com",
    #     "to": ["recipient@example.com"],
    #     "date": "2026-01-15T10:00:00Z",
    #     "has_attachments": true
    # }
    # Example for file:
    # {
    #     "file_type": "pdf",
    #     "file_size": 1024000,
    #     "source_path": "Google Drive/Documents/report.pdf"
    # }

    # Relevance scoring (updated based on usage)
    access_count = Column(Integer, default=0)
    last_accessed_at = Column(String(50), nullable=True)
    relevance_boost = Column(Float, default=1.0)

    # Status
    status = Column(String(50), default="indexed")  # pending, indexed, error, deleted

    # Relationships
    user = relationship("User", back_populates="rag_documents")

    def __repr__(self):
        return f"<RAGDocument {self.source_type}:{self.title[:30] if self.title else 'untitled'}>"
