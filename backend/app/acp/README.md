# ACP (Agent Commerce Protocol) Gateway

## Quick Start

### 1. Seed Agent Identities

Before running tests, seed the agent identities:

```bash
cd backend
python -m app.acp.dev.seed_agents
```

Expected output: `Seeded 50/50 agents`

### 2. Start Backend Server

Start your FastAPI server normally (e.g., `uvicorn app.main:app --reload`)

### 3. Test Manual Request

```bash
curl -X POST http://localhost:8000/acp/submit \
  -H "Content-Type: application/json" \
  -d '{
    "protocol_version": "acp.2025.v1",
    "request_id": "req_test_001",
    "agent_id": "corp_000",
    "agent_signature": "dummy_signature",
    "target_domain": "hotel",
    "target_entity_id": "wrest_point",
    "intent_type": "negotiate",
    "intent_payload": {
      "dates": {"check_in": "2026-03-01", "check_out": "2026-03-03"},
      "room_type": "deluxe_king",
      "guests": 2
    },
    "constraints": {"budget_max": 300, "budget_currency": "AUD"},
    "agent_context": {"reputation_score": 0.8}
  }'
```

Expected response: `{"status": "counter"}` or `{"status": "negotiated"}`

### 4. Run Stress Test

```bash
python tests/synthetic_agents/stress_test_acp.py
```

## Endpoints

- `POST /acp/submit` - Main ACP gateway endpoint
- `POST /acp/register` - Register new agent (for testing)

## Database Files

- `acp_trust.db` - Agent identities and request logs
- `acp_transactions.db` - Transaction state
- `synthetic_hotel.db` - Synthetic hotel availability data

## Architecture

1. **Protocol Layer** (`protocol/gateway_server.py`) - FastAPI endpoint
2. **Trust Layer** (`trust/authenticator.py`) - Authentication & authorization
3. **Transaction Manager** (`transaction/manager.py`) - State management
4. **Negotiation Engine** (`negotiation/engine.py`) - Multi-round negotiation
5. **Domain Adapter** (`domains/hotel/adapter.py`) - Hotel-specific logic
