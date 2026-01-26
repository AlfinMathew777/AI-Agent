# Quick Start Guide

## Starting the System (Every Time)

### Option 1: Automatic Startup (Recommended)
```powershell
.\start.ps1
```

This will:
- ✅ Check dependencies
- ✅ Start backend on port 8002
- ✅ Start frontend on port 5173  
- ✅ Verify health status

### Option 2: Manual Startup

**Terminal 1 - Backend:**
```powershell
cd backend
.\venv\Scripts\python -m uvicorn app.main:app --host 127.0.0.1 --port 8002 --reload
```

**Terminal 2 - Frontend:**
```powershell
cd frontend
npm run dev
```

---

## Testing the Chat (Your Use Case)

1. **Open:** http://localhost:5173
2. **Click:** "Guest Portal" 
3. **Try:** 
   - "Book a room for tomorrow at 7am"
   - "What restaurants are available?"
   - "Reserve a table for 2 people"

If you see connection errors, run:
```powershell
.\health_check.ps1
```

---

## Why Things Break & How We Fixed It

### ❌ Problem 1: "Connection Error"
**Cause:** Backend server stops when PowerShell window closes  
**Fix:** Use `.\start.ps1` which opens persistent windows

### ❌ Problem 2: "Action not found"
**Cause:** Database missing `tenant_id` when creating actions  
**Fix:** ✅ FIXED - Updated `create_action()` to store `tenant_id`

### ❌ Problem 3: Server crashes on restart
**Cause:** Missing dependencies (email-validator)  
**Fix:** ✅ FIXED - Added to `requirements.txt`

### ❌ Problem 4: Hard to test all features
**Fix:** ✅ Created `TESTING_GUIDE.md` with all test cases

---

## Daily Workflow

1. Run `.\start.ps1`
2. Wait for "ready" messages
3. Visit http://localhost:5173
4. Test features using `TESTING_GUIDE.md`
5. To stop: Close PowerShell windows or Ctrl+C

---

## System Status

Check any time:
```powershell
.\health_check.ps1
```

Expected output:
```
✅ Backend: HEALTHY
✅ Frontend: HEALTHY
✅ Database: EXISTS
✅ Environment: CONFIGURED
```

---

## Need More Help?

- **Setup Issues:** See `README.md`
- **Testing:** See `TESTING_GUIDE.md`  
- **Deployment:** See `backend/docs/RUNBOOK.md`
- **Development:** See `backend/docs/workflows.md`
