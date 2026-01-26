# Admin API Testing Commands (Updated)

Before running these tests, ensure you have set the `ADMIN_API_KEY` environment variable in your backend environment (or `.env`).
For these curl commands, replace `$ADMIN_API_KEY` with your actual key value.

## running with Docker (Recommended)
```bash
docker compose up --build
```
Access Frontend: http://localhost:5173
Backend Health: http://localhost:8002/health

## 1. Security Tests

### Test 1a: Admin Key Missing (Server Protection)
# Pre-requisite: Unset ADMIN_API_KEY env var (or don't set it)
# Command:
# curl -i http://localhost:8002/admin/index/status
# Expected: 500 Internal Server Error (Server Misconfiguration: Admin Key Missing) 
# Note: This protects the server from running insecurely if the key isn't configured.

### Test 1b: Key Set but Missing Header
# Pre-requisite: Ensure server is running WITH ADMIN_API_KEY set.
# Command:
curl -i http://localhost:8002/admin/index/status
# Expected: 401 Unauthorized

### Test 1c: Valid Admin Key
# Command:
curl -i -H "x-admin-key: $ADMIN_API_KEY" http://localhost:8002/admin/index/status
# Expected: 200 OK with JSON stats including:
# "last_reindex_time": "2024-..." (ISO string), "last_reindex_error": null

## 2. Reindexing Tests

### Test 2a: Upload Different File Types
# Create dummy files
# NOTE: For PDF testing, please use a REAL .pdf file named test.pdf. 
# Echoing text into a .pdf extension will cause PDF parsers to fail.
echo "TXT content" > test.txt
echo "MD content" > test.md

# Upload them
# curl -H "x-admin-key: $ADMIN_API_KEY" -F "audience=guest" -F "file=@test.pdf" http://localhost:8002/admin/upload
curl -H "x-admin-key: $ADMIN_API_KEY" -F "audience=guest" -F "file=@test.txt" http://localhost:8002/admin/upload
curl -H "x-admin-key: $ADMIN_API_KEY" -F "audience=guest" -F "file=@test.md" http://localhost:8002/admin/upload

### Test 2b: Trigger Full Reindex
# Command:
curl -i -H "x-admin-key: $ADMIN_API_KEY" -X POST "http://localhost:8002/admin/reindex?audience=guest"
# Expected: 200 OK. Backend logs should show indexing of .pdf (if uploaded), .txt, and .md files.

### Test 2c: Verify Status Update
# Command:
curl -i -H "x-admin-key: $ADMIN_API_KEY" http://localhost:8002/admin/index/status
# Expected: "last_reindex_time" should be a recent ISO string.

## 3. Vector Deletion Verification

### Test 3a: Get Initial Count
# Command:
curl -s -H "x-admin-key: $ADMIN_API_KEY" http://localhost:8002/admin/index/status
# Note the "guest_docs" count.

### Test 3b: Delete File
# Command:
curl -i -H "x-admin-key: $ADMIN_API_KEY" -X DELETE "http://localhost:8002/admin/files/guest/test.txt"
# Expected: 200 OK. JSON: { "status": "deleted", "vectors_deleted": <count> }

### Test 3c: Verify Count Decreased
# Command:
curl -s -H "x-admin-key: $ADMIN_API_KEY" http://localhost:8002/admin/index/status
# Expected: "guest_docs" should be less than in Test 3a.

## 4. Bookings API (Phase 4.2)

### Test 4a: List All Bookings
# Command:
curl -H "x-admin-key: $ADMIN_API_KEY" "http://localhost:8002/admin/bookings"
# Expected: list of bookings and summary stats

### Test 4b: Filter by Date & Room Type
# Command (replace Tomorrow with actual date if needed, though tools use "Tomorrow" literal sometimes, real DB uses YYYY-MM-DD usually, but our mock tool might have inserted "Tomorrow" string? Check DB.
# Actually, the tool uses `date` param. `datetime.strptime` in validation expects YYYY-MM-DD. 
# If the tool inserted "Tomorrow", it might fail validation if we try to filter by "Tomorrow" (Wait, validation is only on the QUERY param. If we query by valid date, it checks DB. If DB has "Tomorrow", it won't match "2024-...".)
# However, for testing, if we just want to see it works:
curl -H "x-admin-key: $ADMIN_API_KEY" "http://localhost:8002/admin/bookings?limit=5&order=asc"

### Test 4c: Pagination
# Command:
curl -H "x-admin-key: $ADMIN_API_KEY" "http://localhost:8002/admin/bookings?limit=1&offset=1"

## 5. Tool Stats API (Phase 4.2)

### Test 5a: Default Stats (Last 7 Days)
# Command:
curl -H "x-admin-key: $ADMIN_API_KEY" "http://localhost:8002/admin/tools/stats"
# Expected: JSON with "totals", "by_tool", "recent"

### Test 5b: Filter by Tool Name
# Command:
curl -H "x-admin-key: $ADMIN_API_KEY" "http://localhost:8002/admin/tools/stats?tool=book_room"
# Expected: "by_tool" should only contain "book_room". "totals" reflects only that tool.

### Test 5c: Custom Range (Last 30 Days)
# Command:
curl -H "x-admin-key: $ADMIN_API_KEY" "http://localhost:8002/admin/tools/stats?days=30&limit=5"

## 6. Capacity Rules (Phase 4.2)

### Test 6a: Check Capacity Info
# Ask agent: "Check if standard room is available tomorrow"
# Expected Response: "Start checking... Booked: X/5, Remaining: Y"

### Test 6b: Verify Capacity Enforcement (Manual)
# 1. Edit backend/app/config.py: Set "standard": 1
# 2. Restart backend
# 3. Book 1 room: "Book a standard room..." -> Success
# 4. Book another: "Book a standard room..." -> "Sold out (Booked 1/1)"


## 7. New Backend Structure Tests

The backend has been refactored. Tests are now in `backend/tests/`.

### Run Test Scripts
```bash
python tests/test_endpoint.py
python tests/test_database.py
```

## 8. Agent Workflows (Planner)

### Test 8a: Read-Only Plan
**Request:**
```bash
curl -X POST http://localhost:8002/ask/agent \
  -H "Content-Type: application/json" \
  -d '{"audience": "guest", "question": "Check if standard room available"}'
```
**Expected:** Standard chat response with avail info (internally ran a 1-step plan).

### Test 8b: Multi-step Plan with Confirmation
**1. Request Booking:**
```bash
curl -X POST http://localhost:8002/ask/agent \
  -H "Content-Type: application/json" \
  -d '{"audience": "staff", "question": "Book a standard room"}'
```
**Expected:** JSON with `"status": "needs_confirmation"`, `"action_id": "..."`.

**2. Confirm Booking (Replace ACTION_ID):**
```bash
curl -X POST http://localhost:8002/ask/agent/confirm \
  -H "Content-Type: application/json" \
  -d '{"action_id": "ACTION_ID_HERE", "confirm": true}'
```
**Expected:** Success message "Room booked...".
