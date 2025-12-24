# PROVENIQ Anchors

**The Physical Trust Layer — Backend Service**

Anchors are the infrastructure primitive that binds physical assets to the Proveniq Ledger. This service receives cryptographically signed events from Anchor hardware and writes them to the immutable Ledger.

## Architecture

```
ANCHOR HARDWARE → [This Service] → PROVENIQ LEDGER
                        ↓
              Downstream Consumers
         (Home, Transit, Protect, Capital)
```

## Canonical Events (LOCKED)

| Event | Purpose |
|-------|---------|
| `ANCHOR_REGISTERED` | Bind hardware → asset |
| `ANCHOR_SEAL_ARMED` | Declare asset sealed |
| `ANCHOR_SEAL_BROKEN` | Irreversible integrity breach |
| `ANCHOR_ENVIRONMENTAL_ALERT` | Condition exposure |
| `ANCHOR_CUSTODY_SIGNAL` | Custody handoff |

## Tech Stack

- **Backend:** Python 3.11+ / FastAPI
- **Database:** PostgreSQL (event store)
- **Auth:** Ed25519 signature verification
- **Port:** 8005

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Set up database
alembic upgrade head

# Run development server
uvicorn app.main:app --reload --port 8005
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/events` | Ingest anchor event |
| `GET` | `/api/v1/anchors/{anchor_id}` | Get anchor status |
| `GET` | `/api/v1/anchors/{anchor_id}/events` | Get anchor event history |
| `GET` | `/api/v1/assets/{asset_id}/anchors` | Get anchors for asset |
| `GET` | `/health` | Health check |

## Environment Variables

```env
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/proveniq_anchors
LEDGER_API_URL=http://localhost:8006/api/v1
LEDGER_API_KEY=your-ledger-api-key
```

## License

Proprietary — PROVENIQ Inc.
