# Testing Guide - AI Hotel Assistant

## Quick Start

### 1. Start the System
```powershell
.\start.ps1
```

Wait for both servers to show "ready" messages.

### 2. Open the Application
Visit: http://localhost:5173

---

## Testing All Features

### ✅ Guest Chat (Anonymous)
1. Go to http://localhost:5173
2. Click "Guest Portal"
3. Ask: **"What restaurants are available?"**
4. Expected: List of restaurants with details

### ✅ Room Booking
1. Ask: **"Book a deluxe room for tomorrow"**
2. Expected: Confirmation request with quote
3. Click "Yes, Proceed"
4. Expected: Booking confirmation or payment link

### ✅ Restaurant Reservations
1. Ask: **"Reserve a table for 2 at 7pm tomorrow"**
2. Expected: Available restaurants shown
3. Confirm booking
4. Expected: Reservation confirmed

### ✅ Event Tickets
1. Ask: **"Buy tickets for tonight's show"**
2. Expected: Available events listed
3. Select and confirm
4. Expected: Tickets booked

### ✅ Experience Package
1. Ask: **"Plan a night for 2: dinner + show + room tomorrow"**
2. Expected: Multi-step plan with pricing
3. Confirm
4. Expected: Payment link or full booking

### ✅ Admin Features
1. Go to http://localhost:5173 and click "Login"
2. Login with admin credentials
3. View:
   - Analytics Dashboard
   - Bookings List
   - Commerce Catalog

---

## Common Issues & Fixes

### ❌ "Connection Error" in Chat
**Cause:** Backend not running  
**Fix:** 
```powershell
cd backend
.\venv\Scripts\python -m uvicorn app.main:app --host 127.0.0.1 --port 8002 --reload
```

### ❌ "Quota Exceeded" Error
**Cause:** Google Gemini API rate limit  
**Fix:** Wait a few minutes or use a different API key in `.env`

### ❌ Frontend won't start
**Cause:** Dependencies not installed  
**Fix:**
```powershell
cd frontend
npm install
npm run dev
```

### ❌ "Action not found" on booking
**Cause:** Database or tenant_id issue (FIXED)  
**Fix:** Should work now, but if it happens:
```powershell
cd backend
.\venv\Scripts\python
>>> from app.db.session import init_db
>>> init_db()
>>> exit()
```

---

## Health Checks

### Backend Health
```powershell
curl http://localhost:8002/health
```
Expected: `{"status":"healthy"}`

### API Documentation
Visit: http://localhost:8002/docs

### Database Check
```powershell
cd backend
.\venv\Scripts\python check_db_status.py
```

---

## Running Tests

### All Tests
```powershell
cd backend
.\venv\Scripts\python -m pytest tests/
```

### Specific Feature Tests
```powershell
# Commerce
.\venv\Scripts\python -m pytest tests/test_commerce_e2e.py

# Payments
.\venv\Scripts\python -m pytest tests/test_payments_checkout.py

# Queue
.\venv\Scripts\python -m pytest tests/test_webhook_queue.py

# Planner
.\venv\Scripts\python -m pytest tests/test_planner.py
```

---

## Production Checklist

Before deploying:

- [ ] Environment variables set in `.env`
- [ ] Database initialized (`init_db()`)
- [ ] Stripe webhooks configured
- [ ] Redis running (for queue system)
- [ ] RQ worker running (`python app/queue/worker.py`)
- [ ] All tests passing

---

## Need Help?

1. Check `backend/docs/RUNBOOK.md` for deployment
2. Check `backend/docs/workflows.md` for development workflows
3. Review error logs in terminal windows
