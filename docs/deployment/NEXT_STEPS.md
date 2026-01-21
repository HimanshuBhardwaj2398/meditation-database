# Sprint 2 Phase 3: Deployment & Testing - Detailed Guide

**Status**: Ready to Execute 🚀
**Prerequisites**: Phase 1 ✅ & Phase 2 ✅ Complete
**Estimated Time**: 2-3 hours total

---

## Overview

This guide walks you through deploying the meditation knowledge base to Supabase and verifying the complete end-to-end pipeline. After completing these steps, you'll have:

- ✅ Production PostgreSQL database on Supabase with pgvector
- ✅ Complete schema with documents and chunks tables
- ✅ Alembic migrations for version control
- ✅ Verified database connection and operations
- ✅ Working end-to-end ingestion pipeline

---

## Step-by-Step Implementation

### Step 1: Set Up Supabase Project (10 min)

#### 1.1 Create or Access Supabase Project

1. Go to [Supabase Dashboard](https://supabase.com/dashboard)
2. **Option A**: Create new project
   - Click "New Project"
   - Enter project name: `meditation-knowledge-base`
   - Set database password (save this securely!)
   - Choose region closest to you
   - Click "Create new project"
   - Wait 2-3 minutes for provisioning

3. **Option B**: Use existing project
   - Select your project from dashboard

#### 1.2 Get Database Connection String

1. In your project dashboard, navigate to:
   **Settings → Database → Connection String**

2. Select **Transaction mode** (important!)
   - This uses the connection pooler (port 6543)
   - Better for application connections
   - Example format:
   ```
   postgresql://postgres.PROJECT_REF:PASSWORD@aws-0-REGION.pooler.supabase.com:6543/postgres
   ```

3. Copy the connection string
4. Replace `[YOUR-PASSWORD]` with your actual database password

#### 1.3 Enable pgvector Extension

1. Navigate to: **SQL Editor** in Supabase dashboard
2. Create new query
3. Run this command:
   ```sql
   CREATE EXTENSION IF NOT EXISTS vector;
   ```
4. Verify success:
   ```sql
   SELECT * FROM pg_extension WHERE extname = 'vector';
   ```
   You should see 1 row returned

---

### Step 2: Configure Environment (5 min)

#### 2.1 Update .env File

Edit `/Users/chetna/Desktop/self-projects/meditation-database/.env`:

```bash
# =============================================================================
# SUPABASE DATABASE (Production)
# =============================================================================
DB_URL="postgresql://postgres.PROJECT_REF:YOUR_PASSWORD@aws-0-REGION.pooler.supabase.com:6543/postgres"

# Database pool settings (optimized for Supabase)
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=3600
DB_ECHO=false

# =============================================================================
# API KEYS
# =============================================================================
VOYAGE_API_KEY=your_voyage_api_key_here
LLAMAPARSE_API=your_llamaparse_api_key_here

# Optional
HF_TOKEN=your_huggingface_token_here

# =============================================================================
# CHUNKING & EMBEDDING SETTINGS (defaults are fine)
# =============================================================================
EMBEDDING_VOYAGE_MODEL=voyage-3.5
EMBEDDING_BATCH_SIZE=100
CHUNKING_MAX_SIZE=2000
CHUNKING_MIN_SIZE=700
```

#### 2.2 Verify Configuration

```bash
cd /Users/chetna/Desktop/self-projects/meditation-database

# Test that settings load correctly
poetry run python -c "
from config.settings import get_settings
settings = get_settings()
print(f'Database URL configured: {bool(settings.database.url)}')
print(f'Using Supabase: {settings.database.is_supabase}')
print(f'Pool size: {settings.database.pool_size}')
"
```

Expected output:
```
Database URL configured: True
Using Supabase: True
Pool size: 10
```

---

### Step 3: Set Up Alembic Migrations (15 min)

#### 3.1 Initialize Alembic

```bash
cd /Users/chetna/Desktop/self-projects/meditation-database

# Initialize Alembic (creates alembic/ directory)
poetry run alembic init alembic
```

This creates:
- `alembic/` directory
- `alembic.ini` configuration file
- `alembic/env.py` environment script
- `alembic/versions/` for migration files

#### 3.2 Configure alembic/env.py

Edit `alembic/env.py` and replace its contents with:

```python
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

# Import your models and settings
from db.schema import Base
from config.settings import get_settings

# Alembic Config object
config = context.config

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Add your model's MetaData object here for 'autogenerate' support
target_metadata = Base.metadata

# Get database URL from settings (not alembic.ini)
settings = get_settings()
config.set_main_option("sqlalchemy.url", settings.database.url)


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.

    This configures the context with just a URL and not an Engine.
    Calls to context.execute() emit the given string to the script output.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode.

    In this scenario we need to create an Engine and associate
    a connection with the context.
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

#### 3.3 Update alembic.ini

Edit `alembic.ini` and ensure this line is commented out (we set URL programmatically):

```ini
# sqlalchemy.url = driver://user:pass@localhost/dbname
```

Keep everything else as default.

#### 3.4 Generate Initial Migration

```bash
# Generate migration from current schema
poetry run alembic revision --autogenerate -m "Initial schema: documents and chunks tables"
```

This creates a file like: `alembic/versions/abc123_initial_schema.py`

#### 3.5 Review Generated Migration

Open the generated migration file and verify it contains:

**Upgrade function should include**:
- [ ] Create DocumentStatus enum
- [ ] Create documents table with 12 columns
- [ ] Create chunks table with 7 columns
- [ ] Create foreign key: chunks.document_id → documents.id
- [ ] Create index on documents.status
- [ ] Create index on chunks.document_id

**Common issues to fix manually**:

1. **Enum already exists**: If you get this error, add check in upgrade():
   ```python
   from sqlalchemy.dialects.postgresql import ENUM

   # Create enum only if it doesn't exist
   document_status_enum = ENUM(
       'pending', 'parsing', 'parsed', 'chunking', 'chunked',
       'embedding', 'completed', 'failed',
       name='documentstatus',
       create_type=False  # Don't try to create if exists
   )
   ```

2. **JSONB defaults**: Ensure JSONB fields have proper defaults:
   ```python
   sa.Column('doc_metadata', postgresql.JSONB(), nullable=True, server_default='{}')
   sa.Column('tags', postgresql.ARRAY(sa.Text()), nullable=True, server_default='{}')
   ```

#### 3.6 Apply Migration to Supabase

```bash
# Apply all pending migrations
poetry run alembic upgrade head
```

Expected output:
```
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade  -> abc123, Initial schema: documents and chunks tables
```

#### 3.7 Verify Migration

```bash
# Check current migration version
poetry run alembic current
```

Expected output:
```
abc123 (head)
```

Verify in Supabase:
1. Go to **Table Editor**
2. You should see:
   - `documents` table
   - `chunks` table
   - `alembic_version` table

---

### Step 4: Run Verification Script (5 min)

#### 4.1 Execute Verification

```bash
cd /Users/chetna/Desktop/self-projects/meditation-database

poetry run python scripts/verify_database.py
```

#### 4.2 Expected Output

```
============================================================
Database Setup Verification - Sprint 2 Phase 2
============================================================
1. Testing database connection...
   ✓ Connected to PostgreSQL: PostgreSQL 15.x.x on x86_64-pc-linux-gnu...

2. Checking pgvector extension...
   ✓ pgvector extension is installed

3. Verifying database tables...
   ✓ Table 'documents' exists
   ✓ Table 'chunks' exists

4. Verifying Document table schema...
   ✓ All required columns present

5. Verifying Chunk table schema...
   ✓ All required columns present

6. Testing CRUD operations...
   ✓ Created document (ID: 1)
   ✓ Updated document status
   ✓ Retrieved 1 documents by status
   ✓ Deleted test document

7. Verifying configuration settings...
   ✓ Database URL configured
   ✓ Voyage API Key configured
   ⚠ LlamaParse API Key not set (may be optional)
   ✓ Using Supabase database

============================================================
✓ ALL CHECKS PASSED - Database setup complete!
============================================================
```

#### 4.3 Troubleshooting

**If Check 1 Fails (Connection)**:
- Verify DB_URL in .env is correct
- Check Supabase project is not paused (free tier auto-pauses)
- Verify password doesn't have special characters needing URL encoding
- Try direct connection (port 5432) instead of pooler (port 6543)

**If Check 2 Fails (pgvector)**:
- Run `CREATE EXTENSION IF NOT EXISTS vector;` in Supabase SQL Editor
- Refresh and try again

**If Check 4 or 5 Fails (Schema)**:
- Review generated migration file
- Check if migration was applied: `poetry run alembic current`
- Reapply: `poetry run alembic upgrade head`

**If Check 6 Fails (CRUD)**:
- Check application logs for specific error
- Verify SQLAlchemy models match database schema
- Check database permissions

---

### Step 5: End-to-End Pipeline Test (10 min)

#### 5.1 Test Basic Ingestion

Create test file: `scripts/test_pipeline.py`

```python
"""
Test end-to-end pipeline with Supabase.
"""
import asyncio
import os
from ingestion.orchestrator import IngestionOrchestrator
from ingestion.embed import VectorStoreConfig


async def test_pipeline():
    """Test document ingestion pipeline."""
    print("=" * 60)
    print("Testing End-to-End Pipeline")
    print("=" * 60)

    # Create orchestrator
    orchestrator = IngestionOrchestrator(
        vector_store_config=VectorStoreConfig(
            collection_name='meditation_docs',
            db_url=os.getenv('DB_URL'),
        )
    )

    # Test with a sample URL (replace with real URL)
    source = "https://example.com"
    title = "Test Document"

    print(f"\n1. Processing: {source}")
    print(f"   Title: {title}\n")

    try:
        result = await orchestrator.process(
            source=source,
            title=title
        )

        print("\n" + "=" * 60)
        print("Pipeline Result")
        print("=" * 60)
        print(f"✓ Document ID: {result['document_id']}")
        print(f"✓ Title: {result['title']}")
        print(f"✓ Chunks: {result['chunk_count']}")
        print(f"✓ Success: {result['success']}")
        print(f"\nStage Results:")
        for stage, status in result['stage_results'].items():
            icon = "✓" if status == "completed" else "✗"
            print(f"  {icon} {stage}: {status}")

        if result['errors']:
            print(f"\nErrors:")
            for stage, error in result['errors'].items():
                print(f"  - {stage}: {error}")

        return result['success']

    except Exception as e:
        print(f"\n✗ Pipeline failed: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_pipeline())
    exit(0 if success else 1)
```

Run the test:
```bash
poetry run python scripts/test_pipeline.py
```

#### 5.2 Verify in Database

```bash
poetry run python -c "
from db.database import session_scope
from db.crud import DocumentCRUD, ChunkCRUD

with session_scope() as session:
    # Get all documents
    docs = DocumentCRUD(session).get_all_documents()
    print(f'Total documents: {len(docs)}')

    for doc in docs:
        print(f'\nDocument {doc.id}:')
        print(f'  Title: {doc.title}')
        print(f'  Status: {doc.status.value}')
        print(f'  Source: {doc.file_path}')

        # Get chunks
        chunks = ChunkCRUD(session).get_chunks_by_document(doc.id)
        print(f'  Chunks: {len(chunks)}')

        if chunks:
            print(f'  First chunk preview: {chunks[0].chunk_text[:100]}...')
"
```

#### 5.3 Verify in Supabase Dashboard

1. Go to **Table Editor** → **documents**
2. You should see your test document with status "completed"
3. Click on the document row to see all fields
4. Go to **chunks** table
5. You should see chunk records linked to your document

---

### Step 6: Test Error Handling (5 min)

#### 6.1 Test with Invalid URL

```bash
poetry run python -c "
import asyncio
from ingestion.orchestrator import IngestionOrchestrator
from ingestion.embed import VectorStoreConfig
import os

async def test():
    orchestrator = IngestionOrchestrator(
        vector_store_config=VectorStoreConfig(
            collection_name='meditation_docs',
            db_url=os.getenv('DB_URL'),
        )
    )

    # Try processing invalid URL
    result = await orchestrator.process(
        source='https://this-url-does-not-exist-12345.com',
        title='Test Failed Document'
    )

    print(f'Success: {result[\"success\"]}')
    print(f'Document ID: {result[\"document_id\"]}')
    print(f'Errors: {result[\"errors\"]}')

asyncio.run(test())
"
```

#### 6.2 Verify Failed Document

```bash
poetry run python -c "
from db.database import session_scope
from db.crud import DocumentCRUD

with session_scope() as session:
    failed_docs = DocumentCRUD(session).get_failed_documents()
    print(f'Failed documents: {len(failed_docs)}')

    for doc in failed_docs:
        print(f'\nDocument {doc.id}:')
        print(f'  Title: {doc.title}')
        print(f'  Status: {doc.status.value}')
        print(f'  Error: {doc.status_details}')
"
```

---

### Step 7: Test Resume Functionality (5 min)

#### 7.1 Create Partial Document

```bash
poetry run python -c "
from db.database import session_scope
from db.crud import DocumentCRUD
from db.schema import DocumentStatus

with session_scope() as session:
    # Create document in PENDING state
    doc = DocumentCRUD(session).create_document(
        title='Partial Document',
        file_path='https://example.com/resume-test',
        status=DocumentStatus.PENDING
    )
    print(f'Created document ID: {doc.id}')
    print(f'Status: {doc.status.value}')
    print('\nNow run: poetry run python -c \"import asyncio; from ingestion.orchestrator import IngestionOrchestrator; from ingestion.embed import VectorStoreConfig; import os; asyncio.run(IngestionOrchestrator(vector_store_config=VectorStoreConfig(collection_name=\\'meditation_docs\\', db_url=os.getenv(\\'DB_URL\\'))).process({doc.id}))\"')
"
```

#### 7.2 Resume Processing

Use the command printed above to resume processing the document by ID.

---

## Success Criteria

After completing all steps, you should have:

- ✅ **Supabase Project**: Active with pgvector extension
- ✅ **Database Schema**: documents and chunks tables with all fields
- ✅ **Alembic Setup**: Migrations initialized and applied
- ✅ **Verification**: All 7 checks passing
- ✅ **Pipeline Test**: Successfully processed at least one document
- ✅ **Error Handling**: Failed documents tracked with status_details
- ✅ **Resume Capability**: Can resume partial documents by ID
- ✅ **Database Persistence**: Chunks and metadata saved correctly

---

## Common Issues & Solutions

### Issue 1: Connection Pool Exhausted

**Symptom**:
```
TimeoutError: QueuePool limit of size X overflow Y reached
```

**Solution**:
```bash
# Reduce pool size in .env
DB_POOL_SIZE=5
DB_MAX_OVERFLOW=10
```

### Issue 2: Enum Type Already Exists

**Symptom**:
```
DuplicateObject: type "documentstatus" already exists
```

**Solution**:
Edit migration file and add `create_type=False`:
```python
document_status_enum = ENUM(..., name='documentstatus', create_type=False)
```

### Issue 3: Foreign Key Fails

**Symptom**:
```
IntegrityError: insert or update on table "chunks" violates foreign key constraint
```

**Solution**:
Ensure Document is committed before creating Chunks. The pipeline handles this automatically.

### Issue 4: Supabase Project Paused

**Symptom**:
```
could not connect to server: Connection refused
```

**Solution**:
1. Go to Supabase dashboard
2. Check if project shows "Paused"
3. Click "Restore" to resume (free tier auto-pauses after inactivity)

---

## Next Steps After Phase 3

Once Phase 3 is complete, you can:

1. **Sprint 3: Testing & Polish**
   - Add comprehensive test suite (pytest)
   - Integration tests for full pipeline
   - Performance testing with larger documents

2. **Production Deployment**
   - Set up CI/CD pipeline
   - Configure production environment variables
   - Set up monitoring and alerts

3. **Query Layer (Future)**
   - Build RAG API for semantic search
   - Implement GraphRAG for relationship queries
   - Create application endpoints

---

## References

- [Sprint 2 Implementation Log](../sprints/SPRINT_2_IMPLEMENTATION.md)
- [CHANGELOG](../CHANGELOG.md)
- [ROADMAP](../ROADMAP.md)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [Supabase Documentation](https://supabase.com/docs)
