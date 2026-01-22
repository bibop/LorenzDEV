# LORENZ SaaS Backend

Multi-tenant AI Personal Assistant Platform - FastAPI Backend

## Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 16+
- Redis 7+
- Qdrant (optional, for RAG)

### Development Setup

1. **Clone and setup environment:**

```bash
cd lorenz-backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. **Configure environment:**

```bash
cp .env.example .env
# Edit .env with your settings
```

3. **Start services with Docker:**

```bash
docker-compose up -d postgres redis qdrant
```

4. **Run migrations:**

```bash
alembic upgrade head
```

5. **Start the server:**

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

### Docker Development

Run everything with Docker:

```bash
docker-compose up -d
```

## API Documentation

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Project Structure

```
lorenz-backend/
├── app/
│   ├── api/
│   │   ├── v1/           # API routes
│   │   └── webhooks/     # Webhook handlers
│   ├── models/           # SQLAlchemy models
│   ├── schemas/          # Pydantic schemas
│   ├── services/         # Business logic
│   └── workers/          # Celery tasks
├── alembic/              # Database migrations
├── tests/                # Test suite
└── docker-compose.yml    # Local development
```

## Key Features

- **Multi-tenant Architecture**: Row-Level Security with PostgreSQL
- **OAuth Integration**: Google, Microsoft, LinkedIn, Twitter, Meta
- **Email Integration**: Gmail API, Microsoft Graph, IMAP/SMTP
- **RAG System**: Hybrid search with Qdrant + BM25
- **AI Chat**: Claude integration with streaming
- **Telegram Bot**: Webhook-based bot integration

## Environment Variables

See `.env.example` for all configuration options.

Essential variables:
- `DATABASE_URL`: PostgreSQL connection string
- `SECRET_KEY`: JWT signing key
- `CLAUDE_API_KEY`: Anthropic API key
- OAuth credentials for each provider

## Testing

```bash
pytest
pytest --cov=app  # With coverage
```

## Deployment

For production deployment, see the deployment documentation.

## License

Proprietary - LORENZ SaaS Platform
