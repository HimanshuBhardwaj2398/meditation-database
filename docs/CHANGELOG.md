# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [Unreleased]

### Sprint 2: Pipeline Architecture Patterns (In Progress)

#### Phase 1: Code Refactoring - COMPLETE ✅
- **New**: `core/exceptions.py` - Central exception hierarchy
  - `MeditationDBError` base exception
  - Organized by category: Configuration, Pipeline, Database errors
- **New**: `core/interfaces.py` - Core abstractions
  - `Parser` protocol for parser implementations
  - `ParseResult` dataclass for parser outputs
  - `PipelineStage` ABC for pipeline stages
  - `PipelineContext` with immutable update pattern
  - `StageStatus` enum for execution tracking
- **Refactored**: `ingestion/parsing.py` - Strategy pattern
  - `URLParser` class for HTTP/HTTPS URLs
  - `PDFParser` class for PDF files
  - `ParserFactory` for automatic parser selection
  - Backward-compatible deprecated functions (with warnings)
- **Refactored**: `ingestion/chunking.py` - Thread-safe cache ⚠️ **CRITICAL FIX**
  - `ThreadSafeEmbeddingsCache` singleton with double-checked locking
  - Fixes race conditions with parallel processing
  - Model-specific locks for concurrent loading
- **New**: `ingestion/stages.py` - Individual pipeline stages
  - `ParsingStage` - parse source documents
  - `ChunkingStage` - chunk parsed markdown
  - `EmbeddingStage` - embed and store chunks
- **Refactored**: `ingestion/orchestrator.py` - DAG architecture
  - `PipelineOrchestrator` with topological sort
  - Automatic dependency resolution
  - Cycle detection
  - Backward-compatible `IngestionOrchestrator` API
- **Updated**: `ingestion/__init__.py` - New API exports
  - Maintains backward compatibility with old imports
- **New**: `docs/sprints/` - Sprint documentation
  - Implementation logs and phase guides
  - Referenced from CLAUDE.md for easy access

#### Phase 2: Database Setup - COMPLETE ✅
- **Updated**: `db/schema.py` - Complete schema with all fields
  - Added `file_path`, `status_details`, `chunks` to Document model
  - Added index on `status` column for query optimization
  - **New**: `Chunk` model with full relationships to Document
  - Chunk ↔ LangChain embeddings linking via UUID
- **Updated**: `db/crud.py` - Enhanced CRUD operations
  - Removed broken `EmbeddingCRUD` (referenced non-existent model)
  - Enhanced `DocumentCRUD` with 7 new methods:
    - `update_status()`, `update_markdown()`, `store_chunks()`, `clear_chunks()`
    - `get_documents_by_status()`, `get_failed_documents()`
  - **New**: `ChunkCRUD` class with batch operations
- **Updated**: `config/settings.py` - Supabase optimization
  - Added `pool_timeout`, `pool_recycle` to DatabaseSettings
  - Added `is_supabase` property for environment detection
  - Optimized defaults for Supabase (pool_size=10, max_overflow=20)
- **Updated**: `db/database.py` - Connection pooling
  - Auto-detects Supabase vs local PostgreSQL
  - Supabase-optimized pooling with `pool_pre_ping=True`
  - Enhanced `init_db()` with verification and logging
- **Updated**: `ingestion/stages.py` - UUID tracking and persistence
  - `EmbeddingStage` now adds UUIDs to chunks before embedding
  - **New**: `DatabasePersistenceStage` (Stage 4) - saves chunk metadata
- **Updated**: `ingestion/orchestrator.py` - Database integration
  - Creates Document record at pipeline start
  - Integrates DatabasePersistenceStage as 4th stage
  - Handles FAILED status updates on errors
  - Supports resume by document ID
- **New**: `scripts/verify_database.py` - 7-check verification script
  - Connection, pgvector, tables, schema, CRUD, settings verification

#### Phase 3: Deployment & Testing (Next)
- [ ] Set up Alembic for database migrations
- [ ] Configure Supabase project and apply migrations
- [ ] Run verification script on Supabase
- [ ] End-to-end pipeline testing
- [ ] Update documentation with deployment guide

### Sprint 3: Database & Polish (Planned)
- Alembic database migrations
- Repository pattern for data access
- Unit of Work pattern
- Comprehensive test suite (pytest)
- Docker deployment documentation

---

## [0.2.0] - 2026-01-19

### Added - Sprint 1: Critical Fixes + Docker Setup

#### Configuration Management
- **New**: `config/settings.py` - Centralized Pydantic Settings configuration
  - `DatabaseSettings` - DB connection, pool size, echo mode
  - `EmbeddingSettings` - Voyage AI, HuggingFace models, batch size
  - `ParsingSettings` - LlamaParse API, OCR settings
  - `ChunkingSettings` - Size limits, parallel processing, semantic splitting
  - Backward compatibility with existing env var names (DATABASE_URL, VOYAGE_API_KEY, etc.)
- **New**: `config/__init__.py` - Module exports
- **Updated**: `config.py` - Now delegates to `config/settings.py` for backward compatibility

#### Docker Setup
- **New**: `docker/Dockerfile` - Production multi-stage build
  - Python 3.11-slim base
  - Poetry dependency export
  - Non-root user for security
  - Health check included
- **New**: `docker/Dockerfile.dev` - Development environment
  - All dev dependencies included
  - Volume mounting for hot-reload
- **New**: `docker/docker-compose.yml` - Production compose
  - App service with health check
  - PostgreSQL with pgvector (pgvector/pgvector:pg16)
  - Migration service (profile: migrate)
  - Persistent volumes for data
- **New**: `docker/docker-compose.dev.yml` - Development compose
  - Local PostgreSQL on port 5433
  - pgAdmin web UI (profile: tools)
  - Volume mounting for live code changes
- **New**: `docker/.dockerignore` - Build optimization

#### Environment Configuration
- **New**: `.env.example` - Comprehensive template with:
  - Supabase connection string format
  - Local Docker PostgreSQL format
  - All configurable environment variables
  - Detailed comments explaining each setting

#### Project Configuration
- **Updated**: `pyproject.toml`
  - Fixed project name typo (journalling-assitant → journalling-assistant)
  - Added description
  - Reorganized dependencies by category
  - Added `pydantic-settings` for configuration
  - Added `python-dotenv` (replacing `dotenv`)
  - Added dev dependencies: pytest, pytest-asyncio, pytest-cov, ruff, mypy, alembic
  - Added tool configurations: pytest, ruff, mypy
- **Updated**: `.gitignore` - Comprehensive Python/Docker/IDE exclusions

### Fixed
- **Critical**: Removed hard-coded absolute path in `ingestion/orchestrator.py`
  - Was: `os.chdir("/Users/himanshu/projects/journalling-assitant")`
  - Now: Clean imports without path manipulation

### Changed
- Configuration loading is now centralized through Pydantic Settings
- Environment variables support both new prefixed format and legacy names

---

## [0.1.0] - Initial Release

### Added
- Document ingestion pipeline (parsing, chunking, embedding)
- PostgreSQL + pgvector storage
- LlamaParse PDF processing
- Voyage AI embeddings
- SQLAlchemy ORM with status tracking
- Async chunking with parallel processing
- Basic CRUD operations

---

## File Change Summary (Sprint 1)

| File | Status | Description |
|------|--------|-------------|
| `ingestion/orchestrator.py` | Modified | Removed hard-coded path |
| `config.py` | Modified | Delegates to new settings |
| `config/__init__.py` | New | Module exports |
| `config/settings.py` | New | Pydantic Settings |
| `docker/Dockerfile` | New | Production image |
| `docker/Dockerfile.dev` | New | Development image |
| `docker/docker-compose.yml` | New | Production compose |
| `docker/docker-compose.dev.yml` | New | Dev compose |
| `docker/.dockerignore` | New | Build exclusions |
| `.env.example` | New | Environment template |
| `.gitignore` | Modified | Expanded exclusions |
| `pyproject.toml` | Modified | New dependencies & config |
