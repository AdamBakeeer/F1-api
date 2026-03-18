# 🔧 Fix: Railway DATABASE_URL Not Set

## Problem
Your app is trying to connect to `localhost:5432` instead of Railway's PostgreSQL.

## Solution: Link Services on Railway

### Step 1: In Railway Dashboard
1. Go to your project
2. Click on your **Backend service** (uvicorn)
3. Go to **Variables** tab
4. Look for `DATABASE_URL` — if not there, add it manually

### Step 2: Link PostgreSQL to Backend
**Best way** (automatic environment variables):
1. Click your **Backend service**
2. Go to **Settings** tab
3. Find "Database" or "Services" section
4. Click **"Link Service"**
5. Select your **PostgreSQL service**
6. Railway will auto-create `DATABASE_URL`, `PGHOST`, `PGPORT`, `PGUSER`, `PGPASSWORD`, `PGDATABASE`

### Step 3: Verify DATABASE_URL is Set
1. Go to Backend → Variables
2. Should see `DATABASE_URL=postgresql+psycopg2://user:pass@host:port/dbname`

### Step 4: Redeploy
1. Trigger a new deployment (push code or click Deploy)
2. Check logs for "✓ Using Railway PostgreSQL database"

## What Was Fixed
- ✅ Connection pooling optimized for Railway
- ✅ Better error handling on startup
- ✅ `NullPool` for Railway environment
- ✅ Graceful fallback if schema creation fails

## Quick Check
Run this command locally to test:
```bash
# Set your actual Railway database URL
export DATABASE_URL="postgresql+psycopg2://USER:PASS@HOST:PORT/DBNAME"
python -c "from app.db.database import engine; print(engine.execute('SELECT 1'))"
```

## If Still Failing
1. **Check Railway logs** - exact connection error
2. **Verify PostgreSQL is running** - Railway dashboard shows status
3. **Test connection string** - copy `DATABASE_URL` from Railway and test locally
4. **Check firewall** - Railway should handle this, but verify

---

After linking services and redeploying, your app should connect successfully! 🚀
