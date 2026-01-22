#!/usr/bin/env python3
"""
LORENZ Advanced RAG System
==========================

Production-grade Retrieval-Augmented Generation with:
- Hybrid Search (Vector + BM25)
- Reciprocal Rank Fusion (RRF)
- ColBERT-style Reranking
- Smart Query Routing

Author: Claude Code
Date: 2026-01-13
"""

import os
import logging
import sqlite3
from typing import List, Dict, Tuple, Optional
from datetime import datetime
import json
import numpy as np

# Qdrant
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue

# Embeddings
from sentence_transformers import SentenceTransformer

# BM25
from rank_bm25 import BM25Okapi

# Reranking
try:
    from FlagEmbedding import FlagReranker
    RERANKER_AVAILABLE = True
except ImportError:
    RERANKER_AVAILABLE = False
    logging.warning("FlagEmbedding not available, reranking disabled")

logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURATION
# ============================================================================

QDRANT_HOST = os.getenv('QDRANT_HOST', 'mail.hyperloopitalia.com')
QDRANT_PORT = int(os.getenv('QDRANT_PORT', '6335'))
QDRANT_COLLECTION = 'lorenz_memory'

# Embedding Model (multilingual, 768 dims)
EMBEDDING_MODEL = 'sentence-transformers/paraphrase-multilingual-mpnet-base-v2'

# Reranker Model
RERANKER_MODEL = 'BAAI/bge-reranker-base'

# ============================================================================
# HYBRID SEARCH RAG SYSTEM
# ============================================================================

class LorenzRAG:
    """
    Advanced RAG System with Hybrid Search and Reranking

    Pipeline:
    1. Query → Embedding
    2. Parallel Search:
       - Vector Search (semantic)
       - BM25 Search (keyword)
    3. Fusion: Reciprocal Rank Fusion (RRF)
    4. Reranking: Cross-encoder reranker
    5. Return: Top-K most relevant documents
    """

    def __init__(self, db_path: str, qdrant_host: str = QDRANT_HOST, qdrant_port: int = QDRANT_PORT):
        self.db_path = db_path
        self.qdrant_host = qdrant_host
        self.qdrant_port = qdrant_port

        # Initialize components
        logger.info("🚀 Initializing Lorenz RAG System...")

        # SQLite for metadata and BM25 corpus
        self.db_conn = sqlite3.connect(db_path, check_same_thread=False)
        self._init_database()

        # Qdrant Vector DB
        self.qdrant = QdrantClient(host=qdrant_host, port=qdrant_port)
        self._init_qdrant()

        # Embedding Model (local)
        logger.info(f"📥 Loading embedding model: {EMBEDDING_MODEL}")
        self.encoder = SentenceTransformer(EMBEDDING_MODEL)
        self.embedding_dim = self.encoder.get_sentence_embedding_dimension()

        # Reranker (optional)
        if RERANKER_AVAILABLE:
            logger.info(f"📥 Loading reranker: {RERANKER_MODEL}")
            self.reranker = FlagReranker(RERANKER_MODEL, use_fp16=True)
        else:
            self.reranker = None

        # BM25 Index (loaded on demand)
        self.bm25_index = None
        self.bm25_corpus = []
        self.bm25_ids = []

        logger.info("✅ Lorenz RAG System initialized!")

    def _init_database(self):
        """Initialize SQLite schema for RAG"""
        cursor = self.db_conn.cursor()

        # Documents table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS rag_documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                doc_id TEXT UNIQUE NOT NULL,
                content TEXT NOT NULL,
                metadata TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                embedding_id TEXT
            )
        ''')

        # Index for fast lookup
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_doc_id ON rag_documents(doc_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON rag_documents(timestamp)')

        self.db_conn.commit()
        logger.info("✅ SQLite schema initialized")

    def _init_qdrant(self):
        """Initialize Qdrant collection"""
        try:
            # Check if collection exists
            collections = self.qdrant.get_collections().collections
            collection_names = [c.name for c in collections]

            if QDRANT_COLLECTION not in collection_names:
                # Create collection
                self.qdrant.create_collection(
                    collection_name=QDRANT_COLLECTION,
                    vectors_config=VectorParams(
                        size=self.embedding_dim,
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"✅ Created Qdrant collection: {QDRANT_COLLECTION}")
            else:
                logger.info(f"✅ Qdrant collection exists: {QDRANT_COLLECTION}")

        except Exception as e:
            logger.error(f"❌ Error initializing Qdrant: {e}")
            raise

    def add_document(self, content: str, metadata: Optional[Dict] = None) -> str:
        """
        Add document to RAG system

        Args:
            content: Document text
            metadata: Optional metadata dict

        Returns:
            doc_id: Unique document ID
        """
        try:
            # Generate document ID
            doc_id = f"doc_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"

            # Generate embedding
            embedding = self.encoder.encode(content, convert_to_numpy=True)

            # Store in Qdrant
            self.qdrant.upsert(
                collection_name=QDRANT_COLLECTION,
                points=[
                    PointStruct(
                        id=doc_id,
                        vector=embedding.tolist(),
                        payload={
                            'content': content,
                            'metadata': metadata or {},
                            'timestamp': datetime.now().isoformat()
                        }
                    )
                ]
            )

            # Store in SQLite
            cursor = self.db_conn.cursor()
            cursor.execute('''
                INSERT INTO rag_documents (doc_id, content, metadata, embedding_id)
                VALUES (?, ?, ?, ?)
            ''', (doc_id, content, json.dumps(metadata or {}), doc_id))
            self.db_conn.commit()

            # Invalidate BM25 cache
            self.bm25_index = None

            logger.debug(f"Added document: {doc_id[:20]}...")
            return doc_id

        except Exception as e:
            logger.error(f"Error adding document: {e}")
            raise

    def _build_bm25_index(self):
        """Build BM25 index from SQLite corpus"""
        try:
            cursor = self.db_conn.cursor()
            cursor.execute('SELECT doc_id, content FROM rag_documents ORDER BY timestamp DESC')
            rows = cursor.fetchall()

            self.bm25_ids = [row[0] for row in rows]
            self.bm25_corpus = [row[1] for row in rows]

            # Tokenize corpus
            tokenized_corpus = [doc.lower().split() for doc in self.bm25_corpus]
            self.bm25_index = BM25Okapi(tokenized_corpus)

            logger.info(f"✅ BM25 index built with {len(self.bm25_corpus)} documents")

        except Exception as e:
            logger.error(f"Error building BM25 index: {e}")
            self.bm25_index = None

    def vector_search(self, query: str, top_k: int = 20) -> List[Dict]:
        """Semantic vector search via Qdrant"""
        try:
            # Encode query
            query_vector = self.encoder.encode(query, convert_to_numpy=True)

            # Search in Qdrant
            results = self.qdrant.search(
                collection_name=QDRANT_COLLECTION,
                query_vector=query_vector.tolist(),
                limit=top_k
            )

            # Format results
            documents = []
            for idx, hit in enumerate(results):
                documents.append({
                    'doc_id': hit.id,
                    'content': hit.payload.get('content', ''),
                    'score': hit.score,
                    'rank': idx + 1,
                    'source': 'vector'
                })

            return documents

        except Exception as e:
            logger.error(f"Error in vector search: {e}")
            return []

    def bm25_search(self, query: str, top_k: int = 20) -> List[Dict]:
        """Keyword-based BM25 search"""
        try:
            # Build index if not exists
            if self.bm25_index is None:
                self._build_bm25_index()

            if not self.bm25_index or not self.bm25_corpus:
                return []

            # Tokenize query
            tokenized_query = query.lower().split()

            # Get BM25 scores
            scores = self.bm25_index.get_scores(tokenized_query)

            # Get top-k indices
            top_indices = np.argsort(scores)[::-1][:top_k]

            # Format results
            documents = []
            for rank, idx in enumerate(top_indices):
                if scores[idx] > 0:  # Only non-zero scores
                    documents.append({
                        'doc_id': self.bm25_ids[idx],
                        'content': self.bm25_corpus[idx],
                        'score': float(scores[idx]),
                        'rank': rank + 1,
                        'source': 'bm25'
                    })

            return documents

        except Exception as e:
            logger.error(f"Error in BM25 search: {e}")
            return []

    def reciprocal_rank_fusion(self,
                               vector_results: List[Dict],
                               bm25_results: List[Dict],
                               k: int = 60) -> List[Dict]:
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
            all_doc_ids.add(doc['doc_id'])

        # Calculate RRF scores
        rrf_scores = {}
        doc_contents = {}

        for doc_id in all_doc_ids:
            score = 0.0

            # Vector contribution
            for doc in vector_results:
                if doc['doc_id'] == doc_id:
                    score += 1.0 / (k + doc['rank'])
                    doc_contents[doc_id] = doc['content']
                    break

            # BM25 contribution
            for doc in bm25_results:
                if doc['doc_id'] == doc_id:
                    score += 1.0 / (k + doc['rank'])
                    doc_contents[doc_id] = doc['content']
                    break

            rrf_scores[doc_id] = score

        # Sort by RRF score
        sorted_docs = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)

        # Format output
        fused_results = []
        for rank, (doc_id, score) in enumerate(sorted_docs):
            fused_results.append({
                'doc_id': doc_id,
                'content': doc_contents.get(doc_id, ''),
                'rrf_score': score,
                'rank': rank + 1
            })

        return fused_results

    def rerank(self, query: str, documents: List[Dict], top_k: int = 5) -> List[Dict]:
        """
        Rerank documents using cross-encoder

        Args:
            query: User query
            documents: List of candidate documents
            top_k: Number of top results to return

        Returns:
            Reranked top-k documents
        """
        if not self.reranker or not documents:
            # Return top-k by current score if no reranker
            return documents[:top_k]

        try:
            # Prepare pairs for reranking
            pairs = [[query, doc['content']] for doc in documents]

            # Compute reranking scores
            rerank_scores = self.reranker.compute_score(pairs, normalize=True)

            # Handle single result
            if isinstance(rerank_scores, float):
                rerank_scores = [rerank_scores]

            # Add rerank scores to documents
            for doc, score in zip(documents, rerank_scores):
                doc['rerank_score'] = float(score)

            # Sort by rerank score
            reranked = sorted(documents, key=lambda x: x.get('rerank_score', 0), reverse=True)

            return reranked[:top_k]

        except Exception as e:
            logger.error(f"Error in reranking: {e}")
            return documents[:top_k]

    def hybrid_search(self,
                     query: str,
                     top_k: int = 5,
                     vector_weight: float = 0.5,
                     use_reranking: bool = True) -> List[Dict]:
        """
        Complete hybrid search pipeline

        Args:
            query: User query
            top_k: Number of final results
            vector_weight: Weight for vector vs BM25 (0-1)
            use_reranking: Whether to use reranking

        Returns:
            Top-k most relevant documents
        """
        logger.info(f"🔍 Hybrid search: '{query[:50]}...'")

        # Step 1: Parallel search
        vector_results = self.vector_search(query, top_k=20)
        bm25_results = self.bm25_search(query, top_k=20)

        logger.debug(f"Vector: {len(vector_results)} results, BM25: {len(bm25_results)} results")

        # Step 2: Fusion
        fused_results = self.reciprocal_rank_fusion(vector_results, bm25_results)

        logger.debug(f"Fused: {len(fused_results)} results")

        # Step 3: Reranking
        if use_reranking and self.reranker:
            final_results = self.rerank(query, fused_results[:20], top_k=top_k)
            logger.info(f"✅ Reranked to top-{top_k}")
        else:
            final_results = fused_results[:top_k]
            logger.info(f"✅ Returned top-{top_k} (no reranking)")

        return final_results

    def build_context(self, query: str, max_tokens: int = 2000) -> str:
        """
        Build context from relevant documents for LLM

        Args:
            query: User query
            max_tokens: Maximum context tokens (approx)

        Returns:
            Formatted context string
        """
        # Search for relevant documents
        results = self.hybrid_search(query, top_k=5)

        if not results:
            return ""

        # Build context
        context_parts = []
        total_chars = 0
        max_chars = max_tokens * 4  # Rough estimate: 1 token ≈ 4 chars

        for idx, doc in enumerate(results, 1):
            content = doc['content']

            # Check token limit
            if total_chars + len(content) > max_chars:
                # Truncate last document
                remaining = max_chars - total_chars
                if remaining > 100:  # Only add if substantial
                    context_parts.append(f"[{idx}] {content[:remaining]}...")
                break

            context_parts.append(f"[{idx}] {content}")
            total_chars += len(content)

        context = "\n\n".join(context_parts)

        logger.info(f"📝 Built context: {total_chars} chars from {len(context_parts)} docs")

        return context

    def get_stats(self) -> Dict:
        """Get RAG system statistics"""
        try:
            # SQLite count
            cursor = self.db_conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM rag_documents')
            sqlite_count = cursor.fetchone()[0]

            # Qdrant count
            collection_info = self.qdrant.get_collection(QDRANT_COLLECTION)
            qdrant_count = collection_info.points_count

            return {
                'total_documents': sqlite_count,
                'vector_indexed': qdrant_count,
                'embedding_model': EMBEDDING_MODEL,
                'embedding_dim': self.embedding_dim,
                'reranker_enabled': self.reranker is not None,
                'qdrant_host': f"{self.qdrant_host}:{self.qdrant_port}"
            }

        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {}

# ============================================================================
# QUERY ROUTER
# ============================================================================

class QueryRouter:
    """
    Smart query routing: decide which LLM to use

    Rules:
    - Simple queries → Haiku (cheap, fast)
    - Complex queries → Sonnet (expensive, smart)
    """

    SIMPLE_KEYWORDS = [
        'status', 'come stai', 'ciao', 'cosa', 'quando', 'dove',
        'chi', 'email', 'check', 'mostra', 'list'
    ]

    COMPLEX_KEYWORDS = [
        'analizza', 'spiega', 'perché', 'ottimizza', 'suggerisci',
        'debug', 'confronta', 'strateg', 'implement', 'architett'
    ]

    @staticmethod
    def route(query: str) -> str:
        """
        Route query to appropriate model

        Returns:
            'haiku' or 'sonnet'
        """
        query_lower = query.lower()

        # Check length (long = complex)
        if len(query) > 200:
            return 'sonnet'

        # Check complex keywords
        if any(kw in query_lower for kw in QueryRouter.COMPLEX_KEYWORDS):
            return 'sonnet'

        # Check simple keywords
        if any(kw in query_lower for kw in QueryRouter.SIMPLE_KEYWORDS):
            return 'haiku'

        # Default: Haiku for cost savings
        return 'haiku'

# ============================================================================
# MAIN (for testing)
# ============================================================================

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    # Test RAG system
    rag = LorenzRAG('/opt/lorenz-bot/lorenz_rag.db')

    # Add test documents
    rag.add_document("Il server è in stato operativo normale",
                     {'type': 'status', 'timestamp': '2026-01-13'})

    rag.add_document("NormaOS ha avuto un errore nel container Docker",
                     {'type': 'error', 'service': 'norma'})

    rag.add_document("L'email di bibop@bibop.com contiene 150 messaggi non letti",
                     {'type': 'email', 'account': 'bibop'})

    # Test search
    results = rag.hybrid_search("Qual è lo stato del server?", top_k=3)

    print("\n🔍 Search Results:")
    for doc in results:
        print(f"  - {doc['content'][:80]}... (score: {doc.get('rerank_score', 'N/A')})")

    # Test context building
    context = rag.build_context("Problemi con NormaOS?")
    print(f"\n📝 Context:\n{context}")

    # Stats
    stats = rag.get_stats()
    print(f"\n📊 Stats: {stats}")
