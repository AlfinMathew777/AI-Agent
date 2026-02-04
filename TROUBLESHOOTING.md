# Troubleshooting Guide - AI Hotel Assistant

This guide provides solutions to common issues you may encounter with the AI Hotel Assistant system.

---

## 🚨 Quick Diagnostics

### Step 1: Check System Health
```bash
curl http://localhost:8002/health
```

### Step 2: Run Startup Validation
```bash
cd backend
python scripts/validate_startup.py
```

### Step 3: Check Logs
```bash
# View latest logs
tail -f backend/logs/app.log
```

---

## Common Issues & Solutions

### 1. Server Won't Start

#### Symptom
```
Error: Address already in use
```

####Solution
```bash
# Find process using port 8002
netstat -ano | findstr :8002

# Kill the process (replace PID with actual process ID)
taskkill /PID <PID> /F

# Restart server
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8002
```

---

### 2. Database Connection Errors

#### Symptom
```
DatabaseError: database is locked
```

#### Solution
```bash
# Check if database file exists
ls backend/hotel.db

# If locked, identify blocking process
# Option 1: Restart the server
# Option 2: Check for zombie processes

# Verify database integrity
cd backend
python -c "from app.db.session import get_db_connection; conn = get_db_connection(); print('OK')"
```

---

### 3. AI Service Not Responding

#### Symptom
```
ExternalServiceError: Gemini error: Rate limit exceeded
```

#### Solution
```bash
# Check API key configuration
echo $GOOGLE_API_KEY

# If using quota fallback, wait 60 seconds
# Verify key is valid at: https://makersuite.google.com/app/apikey

# Check health
curl http://localhost:8002/health/ai
```

**Prevention:**
- Implement caching for frequently asked questions
- Use retry logic (already implemented in Phase 2)
- Monitor API usage

---

### 4. Missing Environment Variables

#### Symptom
```
Configuration Error: ADMIN_API_KEY is required!
```

#### Solution
```bash
# Copy example environment file
cp backend/.env.example backend/.env

# Edit with your values
nano backend/.env

# Verify configuration
python scripts/validate_startup.py
```

**Required Variables:**
- `ADMIN_API_KEY` - Admin authentication
- `GOOGLE_API_KEY` - AI service (optional but recommended)

---

### 5. CORS Errors in Frontend

#### Symptom
```
Access to fetch blocked by CORS policy
```

#### Solution
```bash
# Check CORS settings in .env
CORS_ORIGINS=http://localhost:5174,http://localhost:3000

# Restart backend after changing
```

**Verify:**
```bash
curl -H "Origin: http://localhost:5174" \
     -H "Access-Control-Request-Method: GET" \
     -X OPTIONS http://localhost:8002/health
```

---

### 6. ChromaDB Initialization Errors

#### Symptom
```
ChromaDBError: Collection not found
```

#### Solution
```python
# Run reindexing
cd backend
python -c "
from app.services.llm_service import HotelAI
ai = HotelAI()
# Reindex knowledge base
"
```

**Check health:**
```bash
curl http://localhost:8002/health
# Look for ChromaDB component status
```

---

### 7. Import Errors

#### Symptom
```
ModuleNotFoundError: No module named 'fastapi'
```

#### Solution
```bash
# Activate virtual environment
cd backend
call venv\\Scripts\\activate  # Windows
source venv/bin/activate      # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Verify installation
python -c "import fastapi; print(fastapi.__version__)"
```

---

### 8. Slow Response Times

#### Symptom
Requests taking >5 seconds to complete

#### Diagnosis
```bash
# Check database size
ls -lh backend/hotel.db

# Check number of records
python -c "
from app.db.session import get_db_connection
conn = get_db_connection()
cursor = conn.cursor()
cursor.execute('SELECT COUNT(*) FROM chat_logs')
print(f'Chat logs: {cursor.fetchone()[0]}')
"
```

#### Solution
1. **Database optimization:**
   ```sql
   -- Run vacuum
   VACUUM;
   
   -- Analyze tables
   ANALYZE;
   ```

2. **Clear old logs:**
   ```python
   # Delete logs older than 30 days
   DELETE FROM chat_logs WHERE timestamp < date('now', '-30 days');
   ```

3. **Check LLM API latency** - May be external service issue

---

### 9. Health Check Returns 503

#### Symptom
```json
{
  "status": "degraded",
  "components": {
    "database": {"status": "unhealthy"}
  }
}
```

#### Solution
1. **Check specific component:**
   ```bash
   curl http://localhost:8002/health/database
   curl http://localhost:8002/health/ai
   ```

2. **Fix database issues:**
   ```bash
   # Verify database file exists
   ls backend/hotel.db
   
   # Reinitialize if corrupted
   python -c "from app.db.session import init_db; init_db()"
   ```

3. **Fix AI service:**
   ```bash
   # Check API key
   python scripts/validate_startup.py
   ```

---

### 10. Redis Connection Warnings

#### Symptom
```
Warning: Redis not installed - queue functionality will be disabled
```

#### Solution
This is **expected** if Redis is not needed. The system gracefully handles Redis unavailability.

**To install Redis (optional):**
```bash
pip install redis

# Start Redis server (if you want queue functionality)
redis-server
```

---

## 📋 Diagnostic Checklist

When troubleshooting, check these in order:

- [ ] Server is running (`curl http://localhost:8002/health`)
- [ ] Environment variables are set (`.env` file exists)
- [ ] Database file exists (`backend/hotel.db`)
- [ ] Virtual environment is activated
- [ ] Dependencies are installed (`pip list`)
- [ ] Logs show recent activity (`tail -f logs/app.log`)
- [ ] No firewall blocking port 8002
- [ ] API keys are valid

---

## 🔍 Advanced Debugging

### Enable Debug Logging
```bash
# Edit .env
DEBUG=true
LOG_LEVEL=DEBUG

# Restart server
```

### Check All Components
```python
from app.utils.db_utils import health_check_database
from app.utils.redis_utils import health_check_redis
from app.core.config import DB_PATH

print("Database:", health_check_database(DB_PATH))
print("Redis:", health_check_redis())
```

### Monitor Database Queries
```python
# In .env
DATABASE_ECHO=true  # Logs all SQL queries
```

---

## 💡 Getting Help

If issues persist:

1. **Collect diagnostics:**
   ```bash
   python scripts/validate_startup.py > diagnostics.txt
   curl http://localhost:8002/health >> diagnostics.txt
   ```

2. **Check logs:**
   ```bash
   tail -100 logs/app.log > recent_logs.txt
   ```

3. **Share error details:**
   - Error message
   - Steps to reproduce
   - Diagnostic output
   - Log excerpts

---

**Last Updated:** February 4, 2026  
**Version:** Phase 2 Release
