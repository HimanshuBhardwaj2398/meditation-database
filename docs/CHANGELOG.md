# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [Unreleased]

### Sprint 2: Pipeline Architecture Patterns (Planned)
- Strategy pattern for parsers (URL, PDF)
- Parser Factory for automatic parser selection
- Thread-safe caching in chunking module
- DAG-based pipeline orchestrator with resume capability

### Sprint 3: Database & Polish (Planned)
- Alembic database migrations
- Repository pattern for data access
- Basic test suite
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
