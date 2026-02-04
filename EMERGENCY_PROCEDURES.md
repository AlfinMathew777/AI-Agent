# Emergency Procedures - AI Hotel Assistant

**Critical Incident Response Guide**

---

## 🚨 Emergency Contact Information

**System Owner:** [TBD]  
**On-Call Engineer:** [TBD]  
**Escalation:** [TBD]

---

## Emergency Response Levels

### Level 1: Critical (System Down)
- Complete system outage
- Data corruption
- Security breach

**Response Time:** Immediate  
**Action:** Follow Level 1 procedure

### Level 2: High (Degraded Service)
- Partial functionality loss
- Performance severely degraded
- Database lock issues

**Response Time:** Within 30 minutes  
**Action:** Follow Level 2 procedure

### Level 3: Medium (Minor Issues)
- Single component failure
- Slow response times
- API rate limits

**Response Time:** Within 2 hours  
**Action:** Follow Level 3 procedure

---

## Level 1: Critical Incidents

### Complete System Outage

#### 1. Immediate Assessment
```bash
# Check if server is running
curl http://localhost:8002/health

# Check process
tasklist | findstr python

# Check logs
tail -50 backend/logs/app.log
```

#### 2. Emergency Restart
```bash
# Stop any running instances
taskkill /IM python.exe /F

# Start server
cd backend
call venv\\Scripts\\activate
python -m uvicorn app.main:app --host 0.0.0.0 --port 8002
```

#### 3. Verify Recovery
```bash
# Check health
curl http://localhost:8002/health

# Test critical endpoint
curl http://localhost:8002/health/database
```

---

### Database Corruption

#### 1. Stop All Services
```bash
# Stop server immediately
taskkill /F /IM python.exe
```

#### 2. Backup Current State
```bash
# Create backup
copy backend\\hotel.db backend\\hotel.db.corrupted.%date:~-4,4%%date:~-10,2%%date:~-7,2%
```

#### 3. Restore from Backup
```bash
# Restore latest backup
copy backend\\backups\\hotel.db.latest backend\\hotel.db

# Verify integrity
python -c "from app.db.session import get_db_connection; get_db_connection().execute('PRAGMA integrity_check')"
```

#### 4. Restart System
```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8002
```

---

### Security Breach

#### 1. Immediate Lockdown
```bash
# Stop all services
taskkill /F /IM python.exe /IM node.exe

# Revoke API keys (update .env)
ADMIN_API_KEY=NEW_EMERGENCY_KEY_$(date +%s)
GOOGLE_API_KEY=NEW_KEY_FROM_CONSOLE
```

#### 2. Assessment
- Check logs for suspicious activity
- Verify database integrity
- Check for unauthorized access

#### 3. Recovery
- Rotate all credentials
- Review access logs
- Restore from known good backup if needed
- Contact security team

---

## Level 2: High Priority

### Database Locked

#### Quick Fix
```bash
# Identify blocking process
# Restart server
taskkill /F /IM python.exe
sleep 5
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8002
```

#### If Persistent
```python
# Enable WAL mode (should be automatic)
from app.db.session import get_db_connection
conn = get_db_connection()
conn.execute("PRAGMA journal_mode=WAL")
conn.close()
```

---

### Performance Severely Degraded

#### 1. Quick Diagnostics
```bash
# Check database size
ls -lh backend/hotel.db

# Check record counts
python -c "
from app.db.session import get_db_connection
conn = get_db_connection()
for table in ['chat_logs', 'tool_calls', 'bookings']:
    count = conn.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0]
    print(f'{table}: {count}')
"
```

#### 2. Cleanup (if needed)
```sql
-- Delete old logs (>30 days)
DELETE FROM chat_logs WHERE timestamp < date('now', '-30 days');
DELETE FROM tool_calls WHERE created_at < date('now', '-30 days');

-- Vacuum database
VACUUM;
ANALYZE;
```

---

## Level 3: Medium Priority

### AI Service Rate Limited

#### 1. Verify Issue
```bash
curl http://localhost:8002/health/ai
```

#### 2. Temporary Mitigation
```python
# System automatically uses fallback responses
# Wait for quota reset (usually 60 seconds)
# Check API console for quota status
```

#### 3. Long-term Fix
- Review API usage patterns
- Implement caching
- Request quota increase

---

## Rollback Procedures

### Emergency Rollback (Code)

#### 1. Identify Last Good Version
```bash
cd backend
git log --oneline -10
```

#### 2. Rollback Code
```bash
# Create backup of current state
git stash save "emergency_backup_$(date +%Y%m%d_%H%M%S)"

# Rollback to last good commit
git checkout <commit-hash>

# Or rollback one commit
git reset --hard HEAD~1
```

#### 3. Restart Services
```bash
# Stop current
taskkill /F /IM python.exe

# Start with rolled-back code
python -m uvicorn app.main:app --host 0.0.0.0 --port 8002
```

#### 4. Verify
```bash
curl http://localhost:8002/health
```

---

### Database Rollback

#### 1. Stop Services
```bash
taskkill /F /IM python.exe
```

#### 2. Backup Current
```bash
copy backend\\hotel.db backend\\hotel.db.pre-rollback
```

#### 3. Restore Backup
```bash
# List available backups
dir backend\\backups\\

# Restore specific backup
copy backend\\backups\\hotel.db.20260204 backend\\hotel.db
```

#### 4. Verify and Restart
```bash
# Test database
python -c "from app.db.session import get_db_connection; print(get_db_connection().execute('SELECT 1').fetchone())"

# Restart
python -m uvicorn app.main:app --host 0.0.0.0 --port 8002
```

---

## Recovery Checklist

After any emergency procedure:

- [ ] System is responding (`/health` returns 200)
- [ ] Database is accessible
- [ ] AI service is configured
- [ ] Logs show normal operation
- [ ] Critical endpoints tested
- [ ] Backup created of current state
- [ ] Incident documented
- [ ] Root cause identified
- [ ] Prevention measures planned

---

## Post-Incident Actions

### 1. Document Incident
Create incident report with:
- Timestamp of incident
- Level of severity
- Impact description
- Resolution steps taken
- Time to resolution
- Root cause analysis

### 2. Update Monitoring
- Add alerts for similar issues
- Improve health checks
- Update documentation

### 3. Team Communication
- Notify stakeholders
- Schedule post-mortem
- Share learnings

---

## Prevention

### Daily Health Checks
```bash
# Automated daily check
curl http://localhost:8002/health

# Review logs
tail -100 logs/app.log

# Check disk space
df -h
```

### Weekly Maintenance
- Backup database
- Review error logs
- Clean old data
- Update dependencies

### Monthly Review
- Capacity planning
- Performance trends
- Security audit
- Disaster recovery drill

---

**Last Updated:** February 4, 2026  
**Next Review:** March 4, 2026
