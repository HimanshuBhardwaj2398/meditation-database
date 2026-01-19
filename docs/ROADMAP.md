# Development Roadmap

This document outlines the planned development phases for the Journalling Assistant project.

---

## Current Status: Sprint 1 Complete

**Completed**: Critical fixes, Docker setup, centralized configuration

---

## Sprint 2: Pipeline Architecture Patterns

**Goal**: Implement proper design patterns for extensibility and testability

### 2.1 Strategy Pattern for Parsers

**Files to create/modify**:
- `ingestion/parsing.py` - Refactor to Strategy pattern

**Implementation**:
```python
class Parser(Protocol):
    """Protocol for document parsers."""
    def can_parse(self, source: str) -> bool: ...
    def parse(self, source: str) -> ParseResult: ...

class URLParser(Parser):
    """Parser for web URLs."""
    URL_PATTERN = re.compile(r"^https?://", re.IGNORECASE)

    def can_parse(self, source: str) -> bool:
        return bool(self.URL_PATTERN.match(source))

    def parse(self, source: str) -> tuple[str, Optional[str]]:
        # Fetch and convert to markdown
        ...

class PDFParser(Parser):
    """Parser for PDF files using LlamaParse."""

    def can_parse(self, source: str) -> bool:
        return source.lower().endswith(".pdf")

    def parse(self, source: str) -> tuple[str, Optional[str]]:
        # Use LlamaParse
        ...
```

### 2.2 Parser Factory

**Implementation**:
```python
class ParserFactory:
    """Factory for creating appropriate parser based on source type."""

    def __init__(self):
        self._parsers = [URLParser(), PDFParser()]

    def get_parser(self, source: str) -> Parser:
        for parser in self._parsers:
            if parser.can_parse(source):
                return parser
        raise ParsingError(f"No parser for: {source}")
```

### 2.3 Thread-Safe Caching

**Files to modify**:
- `ingestion/chunking.py` - Fix global `_embeddings_cache`

**Current Issue** (line 54):
```python
_embeddings_cache: Dict[str, Any] = {}  # NOT thread-safe!
```

**Solution**:
```python
class ThreadSafeEmbeddingsCache:
    """Thread-safe singleton cache for embedding models."""
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._cache = {}
                    cls._instance._model_locks = {}
        return cls._instance

    def get_embeddings(self, model_name: str) -> HuggingFaceEmbeddings:
        """Get or create embeddings with thread-safe access."""
        ...
```

### 2.4 DAG-Based Pipeline Orchestrator

**Files to create/modify**:
- `ingestion/orchestrator.py` - Refactor to DAG pattern
- `core/interfaces.py` - New file for protocols
- `core/exceptions.py` - New file for exception hierarchy

**Key Components**:

```python
@dataclass
class PipelineContext:
    """Immutable context passed through pipeline stages."""
    document_id: Optional[int] = None
    source: Optional[str] = None
    parsed_content: Optional[str] = None
    title: Optional[str] = None
    chunks: List[Document] = field(default_factory=list)
    stage_results: Dict[str, StageStatus] = field(default_factory=dict)

    def with_update(self, **kwargs) -> "PipelineContext":
        """Create new context with updated fields (immutable)."""
        ...

class PipelineStage(ABC):
    """Abstract base class for idempotent pipeline stages."""

    @property
    @abstractmethod
    def name(self) -> str: ...

    @property
    def required_stages(self) -> List[str]:
        return []

    @abstractmethod
    async def execute(self, context: PipelineContext) -> PipelineContext: ...

    def can_run(self, context: PipelineContext) -> bool:
        """Check if dependencies are satisfied."""
        ...

class PipelineOrchestrator:
    """DAG-based pipeline orchestrator."""

    def __init__(self, stages: List[PipelineStage]):
        self._stages = stages
        self._validate_dag()

    def _topological_sort(self) -> List[PipelineStage]:
        """Sort stages by dependencies."""
        ...

    async def process(self, source: str) -> PipelineResult:
        """Execute pipeline with automatic dependency resolution."""
        ...
```

### 2.5 Exception Hierarchy

**File**: `core/exceptions.py`

```python
class JournallingAssistantError(Exception):
    """Base exception."""

class ConfigurationError(JournallingAssistantError): ...
class PipelineError(JournallingAssistantError): ...
class ParsingError(PipelineError): ...
class ChunkingError(PipelineError): ...
class EmbeddingError(PipelineError): ...
class DatabaseError(JournallingAssistantError): ...
class DocumentNotFoundError(DatabaseError): ...
```

---

## Sprint 3: Database & Polish

**Goal**: Production-ready database management and testing

### 3.1 Alembic Migrations

**Files to create**:
- `alembic.ini` - Alembic configuration
- `migrations/env.py` - Migration environment
- `migrations/versions/001_initial_schema.py` - Initial migration

**Setup**:
```bash
# Initialize Alembic
alembic init migrations

# Create migration
alembic revision --autogenerate -m "Initial schema"

# Run migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

### 3.2 Repository Pattern

**Files to create**:
- `db/repositories.py` - Repository classes
- `db/unit_of_work.py` - Transaction management

**Implementation**:
```python
class DocumentRepository:
    """Repository for Document operations."""

    def __init__(self, session: Session):
        self._session = session

    def create(self, title: str, **kwargs) -> Document: ...
    def get_by_id(self, doc_id: int) -> Document: ...
    def get_by_status(self, status: DocumentStatus) -> List[Document]: ...
    def update_status(self, doc: Document, status: DocumentStatus): ...

class UnitOfWork:
    """Manages transactions across repositories."""

    def __init__(self):
        self._session = None
        self._documents = None

    @property
    def documents(self) -> DocumentRepository:
        if self._documents is None:
            self._documents = DocumentRepository(self._session)
        return self._documents

    def __enter__(self): ...
    def __exit__(self, *args): ...
    def commit(self): ...
    def rollback(self): ...
```

### 3.3 Test Suite

**Files to create**:
```
tests/
├── __init__.py
├── conftest.py           # Shared fixtures
├── unit/
│   ├── __init__.py
│   ├── test_chunking.py
│   ├── test_parsing.py
│   └── test_settings.py
├── integration/
│   ├── __init__.py
│   └── test_pipeline.py
└── e2e/
    ├── __init__.py
    └── test_full_ingestion.py
```

**Key Fixtures** (`conftest.py`):
```python
@pytest.fixture
def test_settings():
    """Override settings for testing."""
    ...

@pytest.fixture
def test_session(test_settings):
    """Create test database session."""
    ...

@pytest.fixture
def sample_markdown():
    """Sample markdown for chunking tests."""
    ...
```

**Running Tests**:
```bash
# All tests
pytest

# With coverage
pytest --cov=. --cov-report=html

# Specific markers
pytest -m unit
pytest -m integration
```

---

## Future Phases

### Phase 2: Query Layer
- RAG API endpoint
- GraphRAG with knowledge graph
- Streaming responses
- Query caching

### Phase 3: Application Integration
- REST API with FastAPI
- Authentication/Authorization
- Rate limiting
- Monitoring (Prometheus/Grafana)

### Phase 4: Scale & Optimize
- Multi-modal support (audio/video)
- Incremental indexing
- Query optimization
- Horizontal scaling

---

## Quick Reference

### Sprint Status

| Sprint | Status | Key Deliverables |
|--------|--------|------------------|
| Sprint 1 | ✅ Complete | Docker, Config, Critical fixes |
| Sprint 2 | 🔲 Planned | Strategy pattern, DAG orchestrator |
| Sprint 3 | 🔲 Planned | Alembic, Repository, Tests |

### Getting Started After Sprint 1

```bash
# Install dependencies
poetry install

# Copy environment config
cp .env.example .env
# Edit .env with your API keys

# Start local PostgreSQL
docker compose -f docker/docker-compose.dev.yml up db -d

# Initialize database
python -c "from db.database import init_db; init_db()"

# Run a test ingestion
python -c "
from ingestion.orchestrator import IngestionOrchestrator
from ingestion import VectorStoreConfig
import asyncio

orchestrator = IngestionOrchestrator(
    vector_store_config=VectorStoreConfig(collection_name='test')
)
# asyncio.run(orchestrator.process('path/to/test.pdf'))
"
```
