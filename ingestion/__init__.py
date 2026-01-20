"""
Ingestion package for document processing pipeline.

Provides both legacy API (deprecated) and new DAG-based pipeline API.
"""

# ============================================================================
# BACKWARD COMPATIBLE EXPORTS (keep for existing code)
# ============================================================================

from .chunking import MarkdownChunker, Config as ChunkingConfig
from .embed import VectorStoreConfig, VectorStoreManager
from .orchestrator import IngestionOrchestrator
from .parsing import html_to_markdown, parse_pdf  # Deprecated


# ============================================================================
# NEW API EXPORTS (Sprint 2 refactoring)
# ============================================================================

# Parsing
from .parsing import ParserFactory, URLParser, PDFParser

# Chunking
from .chunking import ThreadSafeEmbeddingsCache

# Orchestration
from .orchestrator import PipelineOrchestrator, serialize_docs, deserialize_docs

# Pipeline Stages
from .stages import ParsingStage, ChunkingStage, EmbeddingStage


# ============================================================================
# PUBLIC API
# ============================================================================

__all__ = [
    # ===== BACKWARD COMPATIBLE API =====
    # Chunking
    "MarkdownChunker",
    "ChunkingConfig",
    # Embedding
    "VectorStoreConfig",
    "VectorStoreManager",
    # Orchestration
    "IngestionOrchestrator",
    # Parsing (deprecated - use ParserFactory instead)
    "html_to_markdown",
    "parse_pdf",

    # ===== NEW API (Sprint 2) =====
    # Parsing
    "ParserFactory",
    "URLParser",
    "PDFParser",
    # Chunking
    "ThreadSafeEmbeddingsCache",
    # Orchestration
    "PipelineOrchestrator",
    "serialize_docs",
    "deserialize_docs",
    # Pipeline Stages
    "ParsingStage",
    "ChunkingStage",
    "EmbeddingStage",
]
