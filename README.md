# Multi-Source Candidate Data Transformer

A production-quality modular monolith that ingests candidate data from multiple heterogeneous sources (Resume PDFs, Recruiter CSVs, ATS JSON, GitHub/LinkedIn profiles, Recruiter Notes) and transforms them into a single canonical candidate profile with full provenance tracking, deterministic confidence scoring, and configurable projections.

## Architecture

```
React UI → FastAPI Backend → Transformation Engine → PostgreSQL
                                                   ↓
                                             Projection API
                                                   ↓
                                            Explanation API
```

### Design Principles
- **SOLID** — Single Responsibility, Open/Closed, Dependency Inversion
- **Composition over Inheritance** — All pipeline stages use interfaces (ABCs)
- **Dependency Injection** — No global state; all dependencies injected
- **Deterministic Behavior** — No AI, no randomness in scoring or fusion

### Design Patterns
| Pattern | Usage |
|---------|-------|
| Strategy | Parsers, Extractors, Fusion policies, Projection policies |
| Factory | Parser factory selects parser based on file type |
| Adapter | Source adapter normalizes upload metadata |
| Pipeline | Linear transformation: Parse → Extract → Normalize → Fuse → Score → Provenance → Validate |

## Transformation Pipeline

```
Input → Parser → Extractor → Normalizer → Fusion → Confidence → Provenance → Validator → Persistence → Projection
```

Each stage is:
- **Isolated** — Implements an ABC interface
- **Testable** — Pure functions with injected dependencies
- **Replaceable** — Swap regex extractor for LLM extractor without touching downstream

## Tech Stack

### Backend
- Python 3.12, FastAPI, Pydantic v2
- SQLAlchemy 2.x (async), Alembic, PostgreSQL
- pdfplumber (PDF), pytesseract (OCR fallback)
- structlog for logging, pytest for testing

### Frontend
- React 18, TypeScript, Vite
- TailwindCSS v4, Lucide icons
- React Router v6

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Node.js 22+ (for local frontend dev)
- Python 3.12+ (for local backend dev)

### Docker (Recommended)

```bash
# Start everything
docker-compose up --build

# Backend: http://localhost:8000
# Frontend: http://localhost:5173
# API docs: http://localhost:8000/docs
```

### Local Development

```bash
# Backend
cd backend
cp .env.example .env
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

### Database Setup

```bash
# Start PostgreSQL
docker-compose up db

# Run migrations
cd backend
alembic upgrade head
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/transform` | Upload sources, returns canonical profile |
| GET | `/api/candidates` | List all candidates (paginated) |
| GET | `/api/candidate/{id}` | Full candidate detail |
| GET | `/api/candidate/{id}/metadata` | Transformation metadata |
| POST | `/api/candidate/{id}/projection` | Apply projection |
| GET | `/api/candidate/{id}/explain/{field}` | Field explanation |
| GET | `/api/health` | System health check |

## Project Structure

```
backend/
  app/
    api/controllers/     # HTTP handlers (no business logic)
    services/            # Business logic (no SQL)
    repositories/        # Data access (no business logic)
    parsers/             # PDF, CSV, JSON, Text parsers
    extractors/          # Resume regex, structured field extractors
    normalizers/         # Name, email, phone, URL normalizers
    fusion/              # Priority-based + list-merge fusion
    confidence/          # Deterministic scoring engine
    provenance/          # Explanation builder
    projection/          # Configurable profile views
    models/
      domain/            # Core business objects
      dto/               # API request/response models
      database/          # SQLAlchemy ORM models
    interfaces/          # ABC contracts
    factories/           # Parser factory
    adapters/            # Source type adapter
    exceptions/          # Hierarchical exception tree
    middleware/          # Global error handler
    config/              # pydantic-settings
    database/            # Session management
    tests/               # pytest suite

frontend/
  src/
    pages/               # Dashboard, Upload, Candidates, Pipeline, etc.
    components/          # Layout, shared components
    lib/                 # API client
    types/               # TypeScript type definitions
```

## Testing

```bash
cd backend
pytest app/tests/ -v
```

## Key Decisions

1. **Wrong-but-confident is worse than honestly-empty** — All profile fields are Optional. No fabrication.
2. **Deterministic confidence** — Weighted formula: agreement (35%) + priority (25%) + extraction quality (25%) + completeness (15%).
3. **Full provenance** — Every field records: selected source, competing values, selection reason, normalizations applied.
4. **Layered architecture** — Controllers → Services → Repositories → Database. No leaking.
5. **Extractor interface** — Designed so future LLM extractors plug in without modifying fusion/confidence/provenance.

## License

MIT
