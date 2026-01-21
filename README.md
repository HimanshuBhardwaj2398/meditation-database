# Meditation Philosophy Database Layer

A robust database and retrieval infrastructure for meditation philosophy texts. This project provides semantic search capabilities over Buddhist scripture and meditation literature, designed to power various AI tools and assistants focused on contemplative practice.

## Overview

This repository serves as the foundational data layer for a broader ecosystem of meditation-focused AI tools. It provides both the database infrastructure and query layer for AI-assisted contemplative practice applications.

**Current Focus (Phase 1)**: Building the data foundation
- **Document Ingestion**: Parse PDFs and web content into structured markdown
- **Semantic Chunking**: Intelligent text splitting that preserves meaning and context
- **Vector Embeddings**: High-quality embeddings for semantic similarity search
- **PostgreSQL + pgvector**: Scalable vector storage with full SQL capabilities

**Future Focus (Phase 2)**: Query layer with multiple API interfaces (RAG, GraphRAG) for different use cases like meditation journaling, technique guidance, and path exploration.

## Architecture

```
Source Documents (PDF/URL)
         │
         ▼
    ┌─────────┐
    │ PARSING │  LlamaParse (PDF) / HTML-to-Markdown
    └────┬────┘
         │
         ▼
    ┌──────────┐
    │ CHUNKING │  Semantic + Header-based splitting
    └────┬─────┘
         │
         ▼
    ┌───────────┐
    │ EMBEDDING │  Voyage AI embeddings
    └─────┬─────┘
         │
         ▼
    ┌─────────┐
    │ STORAGE │  PostgreSQL + pgvector
    └─────────┘
```

## Project Structure

```
├── db/                      # Database layer
│   ├── database.py          # Connection & session management
│   ├── schema.py            # SQLAlchemy ORM models
│   └── crud.py              # Data access operations
│
├── ingestion/               # Document processing pipeline
│   ├── parsing.py           # PDF/URL parsing utilities
│   ├── chunking.py          # Semantic document chunking
│   ├── embed.py             # Vector embedding & storage
│   └── orchestrator.py      # Pipeline orchestration
│
├── experiments/             # Jupyter notebooks for R&D
│
├── Books/                   # Source texts (Pali Canon)
│   ├── Long Discourses/     # Dīgha Nikāya
│   ├── Medium Discourses/   # Majjhima Nikāya
│   ├── Linked Discourses/   # Saṃyutta Nikāya
│   └── Numbered Discourses/ # Aṅguttara Nikāya
│
└── config.py                # Environment configuration
```

## Tech Stack

| Component | Technology |
|-----------|------------|
| **Database** | PostgreSQL + pgvector |
| **ORM** | SQLAlchemy 2.0 |
| **Embeddings** | Voyage AI (`voyage-3.5`) |
| **PDF Parsing** | LlamaParse |
| **Chunking** | Custom semantic chunker + BAAI/bge-small-en-v1.5 |
| **LLM Framework** | LangChain |
| **Local LLM** | Ollama (optional) |

## Setup

### Prerequisites

- Python 3.11 or 3.12
- PostgreSQL with pgvector extension
- Poetry for dependency management

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd journalling-assistant
   ```

2. **Install dependencies**
   ```bash
   poetry install
   ```

3. **Configure environment variables**

   Create a `.env` file in the project root:
   ```env
   DATABASE_URL=postgresql://user:password@localhost:5432/meditation_db
   LLAMAPARSE_API=your_llamaparse_api_key
   VOYAGE_API_KEY=your_voyage_api_key
   HF_TOKEN=your_huggingface_token  # Optional
   ```

4. **Initialize the database**
   ```python
   from db.database import init_db
   init_db()
   ```

## Usage

### Ingesting Documents

The `IngestionOrchestrator` handles the complete pipeline:

```python
from ingestion.orchestrator import IngestionOrchestrator

orchestrator = IngestionOrchestrator()

# Ingest a PDF
orchestrator.process("path/to/meditation_text.pdf")

# Ingest from URL
orchestrator.process("https://example.com/article")

# Resume failed ingestion by document ID
orchestrator.process(document_id=123)
```

### Document Status Tracking

Documents progress through these states:

```
PENDING → PARSING → PARSED → CHUNKING → CHUNKED → EMBEDDING → COMPLETED
                                                                    │
                                                              (or FAILED)
```

### Chunking Configuration

The `MarkdownChunker` supports customization:

```python
from ingestion.chunking import MarkdownChunker

chunker = MarkdownChunker(
    max_size=2000,           # Maximum chunk size (characters)
    min_size=700,            # Minimum chunk size
    enable_semantic=True,    # Enable semantic splitting
    enable_parallel=True,    # Parallel processing
    max_workers=4
)

chunks = await chunker.chunk(markdown_content, doc_title="Satipatthana Sutta")
```

### Direct Database Access

```python
from db.database import session_scope
from db.crud import DocumentCRUD

with session_scope() as session:
    crud = DocumentCRUD(session)

    # Create a document
    doc = crud.create_document(
        title="Anapanasati Sutta",
        markdown="...",
        tags=["breathing", "mindfulness"]
    )

    # Retrieve documents
    all_docs = crud.get_all_documents()
```

## Source Texts

This project includes translations of the Pali Canon by Bhikkhu Sujato:

- **Dīgha Nikāya** (Long Discourses) - Extended teachings on meditation and philosophy
- **Majjhima Nikāya** (Medium Discourses) - Core meditation instructions
- **Saṃyutta Nikāya** (Linked Discourses) - Thematically organized teachings
- **Aṅguttara Nikāya** (Numbered Discourses) - Progressive numerical collections

## Roadmap

### Phase 1: Data Layer (Current)
- [x] PDF and web content parsing pipeline
- [x] Semantic chunking with context preservation
- [x] Vector embedding and storage (Voyage AI + pgvector)
- [x] Document status tracking and resume capabilities
- [ ] Incremental indexing for new content
- [ ] Additional text traditions (Zen, Tibetan, Vedantic literature)

### Phase 2: Query Layer (Upcoming)
- [ ] **RAG API**: Simple semantic search with context-aware retrieval
  - Citation tracking back to source suttas
  - Relevance scoring and ranking
  - Streaming responses for long-form answers
- [ ] **GraphRAG API**: Relationship-aware queries with multi-hop reasoning
  - Knowledge graph construction from chunks
  - Entity extraction (concepts, practices, teachers)
  - Conceptual connections and prerequisite relationships
- [ ] **Custom Query APIs**: Specialized endpoints for specific use cases
  - Technique-specific searches
  - Practice progression tracking
  - Personalized recommendations

### Phase 3: Application Integration
- [ ] **Meditation Journaling App**: Suggest relevant teachings based on journal entries
- [ ] **Practice Guidance Tool**: Answer technique questions with citations
- [ ] **Path Exploration Interface**: Navigate interconnected concepts
- [ ] **Daily Reflection Generator**: Contextual wisdom for specific situations
- [ ] Multi-modal support (audio dharma talks, video transcripts)

## License

This project is for personal and educational use. The included Buddhist texts are translations by Bhikkhu Sujato, available under Creative Commons.
