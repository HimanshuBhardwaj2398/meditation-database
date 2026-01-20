# Sprint 2 - Phase 2: Database Setup Guide

**Status**: Ready to Start
**Prerequisites**: Phase 1 Complete ✅

---

## Overview

Phase 2 focuses on updating the database schema to include all fields required by the refactored orchestrator, and initializing a fresh Supabase database with the complete schema.

**Key Difference from Original Plan**: We're creating a fresh schema on Supabase (not migrating existing data), so no complex migrations are needed.

---

## Tasks

### Task 2.1: Update Schema Definition

**File**: [db/schema.py](../../db/schema.py)
**Status**: Pending

#### Current Schema (Missing Fields)

```python
class Document(Base):
    __tablename__ = "documents"

    id = Column(BigInteger, primary_key=True)
    title = Column(Text, nullable=False)
    markdown = Column(Text)
    doc_metadata = Column(JSONB)
    tags = Column(ARRAY(Text))
    status = Column(Enum(DocumentStatus, ...), default=DocumentStatus.PENDING)
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
```

#### Required Changes

Add these three fields:

```python
class Document(Base):
    __tablename__ = "documents"

    id = Column(BigInteger, primary_key=True)
    title = Column(Text, nullable=False)

    # ADD THIS:
    file_path = Column(Text, nullable=True)  # Source file path or URL

    markdown = Column(Text)
    doc_metadata = Column(JSONB)
    tags = Column(ARRAY(Text))
    status = Column(Enum(DocumentStatus, ...), default=DocumentStatus.PENDING)

    # ADD THIS:
    status_details = Column(Text, nullable=True)  # Error messages from failed stages

    # ADD THIS:
    chunks = Column(JSONB, nullable=True)  # Temporary storage before embedding

    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
```

**Field Descriptions**:
- `file_path`: Stores the original source (URL or file path) for reference and resume capability
- `status_details`: Stores error messages when stages fail (e.g., "Parsing failed: File not found")
- `chunks`: Temporary JSON storage for serialized chunks between chunking and embedding stages

**All fields are nullable** to avoid breaking any future schema changes.

---

### Task 2.2: Update CRUD Operations

**File**: [db/crud.py](../../db/crud.py)
**Status**: Pending

#### Add file_path Parameter

Update `create_document()` to accept `file_path`:

```python
class DocumentCRUD:
    def create_document(
        self,
        title: str,
        markdown: str,
        file_path: Optional[str] = None,  # ADD THIS
        tags: list[str] = None,
        doc_metadata: dict = None,
        description: str = None,
    ):
        """Creates a new document and stores it in the database."""
        db_document = schema.Document(
            title=title,
            markdown=markdown,
            file_path=file_path,  # ADD THIS
            tags=tags,
            doc_metadata=doc_metadata,
            description=description,
        )
        self.db.add(db_document)
        self.db.commit()
        self.db.refresh(db_document)
        return db_document
```

#### Add Helper Methods

Add these convenience methods:

```python
class DocumentCRUD:
    # ... existing methods ...

    def update_status(
        self,
        document_id: int,
        status: schema.DocumentStatus,
        details: Optional[str] = None
    ) -> Optional[schema.Document]:
        """
        Update document status and status details.

        Args:
            document_id: ID of document to update
            status: New status value
            details: Optional status details (e.g., error message)

        Returns:
            Updated document or None if not found
        """
        doc = self.get_document_by_id(document_id)
        if doc:
            doc.status = status
            doc.status_details = details
            self.db.commit()
            self.db.refresh(doc)
        return doc

    def get_documents_by_status(
        self,
        status: schema.DocumentStatus
    ) -> List[schema.Document]:
        """
        Get all documents with a specific status.

        Args:
            status: Status to filter by

        Returns:
            List of documents with matching status
        """
        return self.db.query(schema.Document).filter(
            schema.Document.status == status
        ).all()

    def clear_chunks(self, document_id: int) -> Optional[schema.Document]:
        """
        Clear temporary chunks field after successful embedding.

        Args:
            document_id: ID of document

        Returns:
            Updated document or None if not found
        """
        doc = self.get_document_by_id(document_id)
        if doc:
            doc.chunks = None
            self.db.commit()
            self.db.refresh(doc)
        return doc
```

---

### Task 2.3: Initialize Supabase Database

**Prerequisites**:
- Supabase project created
- Connection string available

#### Step 1: Set Environment Variable

Add to your `.env` file:

```bash
DATABASE_URL="postgresql://postgres:[YOUR-PASSWORD]@db.[YOUR-PROJECT-REF].supabase.co:5432/postgres"
```

**How to get this**:
1. Go to your Supabase project dashboard
2. Click "Settings" → "Database"
3. Find "Connection string" → "URI"
4. Copy and paste (replace `[YOUR-PASSWORD]` with your database password)

#### Step 2: Verify Connection

Test the connection:

```bash
poetry run python -c "
from db.database import engine
from sqlalchemy import text
with engine.connect() as conn:
    result = conn.execute(text('SELECT version()'))
    print('✓ Connected to:', result.fetchone()[0])
"
```

#### Step 3: Initialize Database

Run the initialization:

```bash
poetry run python -c "from db.database import init_db; init_db()"
```

**What This Does**:
1. Creates `pgvector` extension
2. Creates `documents` table with all fields (including new ones)
3. Creates `chunks` table (if defined in schema)
4. Creates indexes
5. Sets up constraints

#### Step 4: Verify Schema

Check that all fields exist:

```bash
poetry run python -c "
from db.schema import Document
fields = [c.name for c in Document.__table__.columns]
print('Document fields:', fields)

# Should see: file_path, status_details, chunks
required = ['file_path', 'status_details', 'chunks']
missing = [f for f in required if f not in fields]
if missing:
    print('❌ Missing fields:', missing)
else:
    print('✓ All required fields present')
"
```

You can also verify in Supabase dashboard:
1. Go to "Table Editor"
2. Select "documents" table
3. Check columns list

---

## Verification Checklist

After completing Phase 2:

- [ ] `file_path` column exists in `documents` table
- [ ] `status_details` column exists in `documents` table
- [ ] `chunks` column exists in `documents` table
- [ ] CRUD `create_document()` accepts `file_path` parameter
- [ ] CRUD `update_status()` method works
- [ ] CRUD `get_documents_by_status()` method works
- [ ] Can connect to Supabase from application
- [ ] `init_db()` runs without errors
- [ ] pgvector extension is enabled

---

## Common Issues & Solutions

### Issue 1: Connection Refused

**Error**: `could not connect to server: Connection refused`

**Solution**: Check that:
- DATABASE_URL is correct
- Supabase project is not paused
- Network connection is stable
- Firewall allows PostgreSQL connections

### Issue 2: pgvector Extension Missing

**Error**: `extension "vector" does not exist`

**Solution**: Run in Supabase SQL Editor:
```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

### Issue 3: Permission Denied

**Error**: `permission denied for schema public`

**Solution**: Your database user needs proper permissions. Run:
```sql
GRANT ALL ON SCHEMA public TO postgres;
GRANT ALL ON ALL TABLES IN SCHEMA public TO postgres;
```

---

## Next Steps After Phase 2

Once Phase 2 is complete, move to **Phase 3: Integration & Testing**:

1. Add `DatabasePersistenceStage` to save pipeline results
2. Update orchestrator to use database persistence
3. Create comprehensive verification script
4. End-to-end testing with Supabase

---

## References

- **Implementation Log**: [SPRINT_2_IMPLEMENTATION.md](SPRINT_2_IMPLEMENTATION.md)
- **Schema File**: [db/schema.py](../../db/schema.py)
- **CRUD File**: [db/crud.py](../../db/crud.py)
- **Database Module**: [db/database.py](../../db/database.py)
