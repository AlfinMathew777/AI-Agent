# Agent Workflows & Planner

## Overview
The Agent now supports multi-step workflows using a **Planner + Runner** architecture. This allows complex requests (e.g. "Book a room") to be broken down into sequential steps, ensuring safety with **WRITE confirmation**.

## Architecture

### 1. Hybrid Planner (`agent/planner/planner.py`)
- Analyzes user request.
- Uses **Rules-based logic** (for MVP) to detect common intents.
- Falls back to Legacy Router/LLM if no rule matches.
- Produces a `Plan` object with ordered `PlanSteps`.

### 2. Plan Runner (`agent/planner/runner.py`)
- Executes steps sequentially.
- **READ** steps (e.g. `check_availability`) run immediately.
- **WRITE** steps (e.g. `book_room`) suspend execution and return `needs_confirmation`.
- Can **Resume** execution after user confirmation.

### 3. Database (`tables: plans, plan_steps`)
- Stores plan state and history.
- Tracks step status (pending, running, success, failed).

## Workflow Lifecycle

1. **User Request**: `POST /ask/agent`
2. **Planning**: Agent generates a Plan (e.g. Step 1: Check, Step 2: Book).
3. **Execution**:
   - Runner executes Step 1 (READ). Success.
   - Runner hits Step 2 (WRITE).
   - Agent returns `{ status: "needs_confirmation", action_id: "...", ... }`.
4. **Confirmation**: `POST /ask/agent/confirm` `{ action_id: "...", confirm: true }`
5. **Resumption**:
   - Agent executes Step 2 (WRITE).
   - Agent completes plan.
   - Returns final "Success" message.

## Usage

### Agent Request
```json
POST /ask/agent
{
  "audience": "staff",
  "question": "Book a standard room for tomorrow"
}
```

### Response (Confirmation Needed)
```json
{
  "status": "needs_confirmation",
  "action_id": "uuid...",
  "plan_id": "uuid...",
  "message": "I need approval to book_room..."
}
```

### Confirm & Execute
```json
POST /ask/agent/confirm
{
  "action_id": "uuid...",
  "confirm": true
}
```
