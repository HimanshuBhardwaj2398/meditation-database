"""
Core foundational modules for the meditation database.

This package contains central abstractions, exceptions, and interfaces
used throughout the application.
"""

from .exceptions import (
    MeditationDBError,
    ConfigurationError,
    PipelineError,
    ParsingError,
    ChunkingError,
    EmbeddingError,
    DatabaseError,
    DocumentNotFoundError,
    SchemaValidationError,
)

from .interfaces import (
    ParseResult,
    Parser,
    StageStatus,
    PipelineContext,
    PipelineStage,
)

__all__ = [
    # Exceptions
    "MeditationDBError",
    "ConfigurationError",
    "PipelineError",
    "ParsingError",
    "ChunkingError",
    "EmbeddingError",
    "DatabaseError",
    "DocumentNotFoundError",
    "SchemaValidationError",
    # Interfaces
    "ParseResult",
    "Parser",
    "StageStatus",
    "PipelineContext",
    "PipelineStage",
]
