"""
Pipeline stages for document ingestion.

Each stage is idempotent and declares its dependencies.
Stages receive a PipelineContext and return an updated context.
"""

import logging
import uuid as uuid_lib
from typing import List

from core.interfaces import PipelineStage, PipelineContext, StageStatus
from core.exceptions import ParsingError, ChunkingError, EmbeddingError, DatabaseError
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
            # Add UUIDs and metadata to each chunk BEFORE embedding
            for idx, chunk in enumerate(context.chunks):
                # Generate UUID for linking with database
                chunk_uuid = str(uuid_lib.uuid4())

                # Add to metadata
                chunk.metadata["uuid"] = chunk_uuid
                chunk.metadata["original_doc_id"] = context.document_id
                chunk.metadata["original_doc_title"] = context.title
                chunk.metadata["chunk_index"] = idx

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


# ============================================================================
# STAGE 4: DATABASE PERSISTENCE
# ============================================================================

class DatabasePersistenceStage(PipelineStage):
    """
    Stage 4: Save document and chunk metadata to database.

    Dependencies: embedding
    Input: context.document_id, context.chunks (with UUIDs from vector store)
    Output: Chunks saved to database, document status updated to COMPLETED
    """

    @property
    def name(self) -> str:
        return "database_persistence"

    @property
    def required_stages(self) -> List[str]:
        return ["embedding"]

    async def execute(self, context: PipelineContext) -> PipelineContext:
        """
        Save document and chunk metadata to database.

        Args:
            context: Pipeline context with embedded chunks

        Returns:
            Context marked as persistence completed

        Raises:
            DatabaseError: If database operations fail
        """
        from db.database import session_scope
        from db.crud import DocumentCRUD, ChunkCRUD
        from db.schema import DocumentStatus

        if not context.document_id:
            raise DatabaseError("No document_id in context")

        if not context.chunks:
            logger.warning("No chunks to persist")
            return context.mark_stage_completed(self.name)

        logger.info(f"Persisting {len(context.chunks)} chunks to database")

        try:
            with session_scope() as session:
                doc_crud = DocumentCRUD(session)
                chunk_crud = ChunkCRUD(session)

                # Prepare chunk data for database
                chunks_data = []
                for idx, chunk in enumerate(context.chunks):
                    # Extract UUID from metadata (added by EmbeddingStage)
                    chunk_uuid = chunk.metadata.get("uuid")
                    if not chunk_uuid:
                        # Generate UUID if not present (shouldn't happen)
                        chunk_uuid = str(uuid_lib.uuid4())
                        logger.warning(
                            f"Chunk {idx} missing UUID, generated: {chunk_uuid}"
                        )

                    chunks_data.append({
                        "uuid": chunk_uuid,
                        "chunk_text": chunk.page_content,
                        "chunk_index": idx,
                        "chunk_metadata": chunk.metadata,
                    })

                # Save chunks to database
                created_chunks = chunk_crud.create_chunks_batch(
                    document_id=context.document_id,
                    chunks_data=chunks_data,
                )

                logger.info(f"✓ Saved {len(created_chunks)} chunks to database")

                # Update document status to COMPLETED
                doc_crud.update_status(
                    document_id=context.document_id,
                    status=DocumentStatus.COMPLETED,
                    status_details=f"Successfully processed {len(created_chunks)} chunks",
                )

                # Clear temporary chunk storage
                doc_crud.clear_chunks(context.document_id)

                logger.info(f"✓ Document {context.document_id} marked as COMPLETED")

            return context.mark_stage_completed(self.name)

        except DatabaseError as e:
            logger.error(f"Database persistence failed: {e}")
            return context.mark_stage_failed(self.name, str(e))
        except Exception as e:
            logger.error(f"Unexpected error in persistence stage: {e}", exc_info=True)
            return context.mark_stage_failed(self.name, f"Unexpected error: {e}")
