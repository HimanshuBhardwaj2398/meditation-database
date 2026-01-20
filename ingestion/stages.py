"""
Pipeline stages for document ingestion.

Each stage is idempotent and declares its dependencies.
Stages receive a PipelineContext and return an updated context.
"""

import logging
from typing import List

from core.interfaces import PipelineStage, PipelineContext, StageStatus
from core.exceptions import ParsingError, ChunkingError, EmbeddingError
from ingestion.parsing import ParserFactory
from ingestion.chunking import MarkdownChunker, Config as ChunkingConfig
from ingestion.embed import VectorStoreManager

logger = logging.getLogger(__name__)


# ============================================================================
# STAGE 1: PARSING
# ============================================================================

class ParsingStage(PipelineStage):
    """
    Stage 1: Parse source document into markdown.

    Dependencies: None
    Input: context.source (file path or URL)
    Output: context.parsed_content, context.title
    """

    def __init__(self, parser_factory: ParserFactory):
        """
        Initialize parsing stage.

        Args:
            parser_factory: Factory for creating appropriate parsers
        """
        self.parser_factory = parser_factory

    @property
    def name(self) -> str:
        return "parsing"

    @property
    def required_stages(self) -> List[str]:
        return []  # No dependencies

    async def execute(self, context: PipelineContext) -> PipelineContext:
        """
        Parse source document and update context.

        Args:
            context: Pipeline context with source

        Returns:
            Context with parsed_content and title populated

        Raises:
            ParsingError: If parsing fails
        """
        if not context.source:
            raise ParsingError("No source provided in context")

        logger.info(f"Parsing source: {context.source}")

        try:
            # Use ParserFactory to automatically select parser
            result = self.parser_factory.parse(context.source)

            logger.info(f"Successfully parsed: {context.source} (title: {result.title})")

            # Update context with parsed results
            return context.with_update(
                parsed_content=result.content,
                title=result.title or "Untitled"
            ).mark_stage_completed(self.name)

        except ParsingError as e:
            logger.error(f"Parsing failed: {e}")
            return context.mark_stage_failed(self.name, str(e))
        except Exception as e:
            logger.error(f"Unexpected error in parsing stage: {e}", exc_info=True)
            return context.mark_stage_failed(self.name, f"Unexpected error: {e}")


# ============================================================================
# STAGE 2: CHUNKING
# ============================================================================

class ChunkingStage(PipelineStage):
    """
    Stage 2: Chunk parsed markdown into semantic segments.

    Dependencies: parsing
    Input: context.parsed_content, context.title
    Output: context.chunks
    """

    def __init__(self, chunking_config: ChunkingConfig):
        """
        Initialize chunking stage.

        Args:
            chunking_config: Configuration for chunking behavior
        """
        self.chunking_config = chunking_config

    @property
    def name(self) -> str:
        return "chunking"

    @property
    def required_stages(self) -> List[str]:
        return ["parsing"]

    async def execute(self, context: PipelineContext) -> PipelineContext:
        """
        Chunk parsed content into semantic segments.

        Args:
            context: Pipeline context with parsed content

        Returns:
            Context with chunks populated

        Raises:
            ChunkingError: If chunking fails
        """
        if not context.parsed_content:
            raise ChunkingError("No parsed content available for chunking")

        logger.info(f"Chunking document: {context.title}")

        try:
            chunker = MarkdownChunker(
                text=context.parsed_content,
                config=self.chunking_config,
                title=context.title
            )

            chunks, stats = await chunker.chunk()

            logger.info(
                f"Chunking complete: {stats.total_chunks} chunks in "
                f"{stats.processing_time:.2f}s (avg {stats.avg_chunk_size:.0f} words)"
            )

            return context.with_update(
                chunks=chunks
            ).mark_stage_completed(self.name)

        except ChunkingError as e:
            logger.error(f"Chunking failed: {e}")
            return context.mark_stage_failed(self.name, str(e))
        except Exception as e:
            logger.error(f"Unexpected error in chunking stage: {e}", exc_info=True)
            return context.mark_stage_failed(self.name, f"Unexpected error: {e}")


# ============================================================================
# STAGE 3: EMBEDDING
# ============================================================================

class EmbeddingStage(PipelineStage):
    """
    Stage 3: Embed chunks and store in vector database.

    Dependencies: chunking
    Input: context.chunks, context.document_id, context.title
    Output: Chunks stored in vector database
    """

    def __init__(self, vector_store_manager: VectorStoreManager):
        """
        Initialize embedding stage.

        Args:
            vector_store_manager: Manager for vector store operations
        """
        self.vector_store_manager = vector_store_manager

    @property
    def name(self) -> str:
        return "embedding"

    @property
    def required_stages(self) -> List[str]:
        return ["chunking"]

    async def execute(self, context: PipelineContext) -> PipelineContext:
        """
        Embed chunks and store in vector database.

        Args:
            context: Pipeline context with chunks

        Returns:
            Context marked as embedding completed

        Raises:
            EmbeddingError: If embedding fails
        """
        if not context.chunks:
            raise EmbeddingError("No chunks available for embedding")

        logger.info(f"Embedding {len(context.chunks)} chunks")

        try:
            # Add document metadata to each chunk
            for chunk in context.chunks:
                chunk.metadata["original_doc_id"] = context.document_id
                chunk.metadata["original_doc_title"] = context.title

            # Embed and store in vector database
            vector_ids = self.vector_store_manager.embed_documents(context.chunks)

            if len(vector_ids) != len(context.chunks):
                logger.warning(
                    f"Embedding mismatch: {len(context.chunks)} chunks, "
                    f"{len(vector_ids)} embeddings stored"
                )

            logger.info(f"Successfully embedded {len(vector_ids)} chunks")

            return context.mark_stage_completed(self.name)

        except EmbeddingError as e:
            logger.error(f"Embedding failed: {e}")
            return context.mark_stage_failed(self.name, str(e))
        except Exception as e:
            logger.error(f"Unexpected error in embedding stage: {e}", exc_info=True)
            return context.mark_stage_failed(self.name, f"Unexpected error: {e}")
