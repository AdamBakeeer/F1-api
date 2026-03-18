# 🚂 Railway Deployment Guide for F1 API

This guide walks you through deploying the F1 API and Frontend on Railway.

## Prerequisites

- Railway account (https://railway.app)
- GitHub repository connected to Railway (recommended)
- PostgreSQL database (Railway can provision this)

## Step 1: Set Up on Railway

### 1.1 Create a New Railway Project

1. Go to [Railway Dashboard](https://railway.app/dashboard)
2. Click "New Project"
3. Select "Deploy from GitHub" or "Empty Project"
4. If GitHub: authorize and select your `F1-api` repository

### 1.2 Add PostgreSQL Database

1. In your Railway project, click "+ New Service"
2. Select "Database" → "PostgreSQL"
3. Wait for PostgreSQL to initialize
4. Railway will automatically set `$DATABASE_URL` environment variable

## Step 2: Configure Environment Variables

In your Railway project settings, add the following environment variables:

### Backend Environment Variables

```
# Database (auto-set by Railway PostgreSQL addon)
DATABASE_URL=postgresql+psycopg2://user:password@host:5432/railway

# Security & Authentication
SECRET_KEY=<generate-a-long-random-string>
ADMIN_USERNAME=admin@example.com
ADMIN_PASSWORD=<set-a-strong-password>

# CORS (update with your production domain)
ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# PORT (Railway sets this automatically, but you can override)
PORT=8000
```

### To Generate a Strong SECRET_KEY

Run this in your terminal:
```bash
openssl rand -hex 32
```

Or use Python:
```python
import secrets
print(secrets.token_hex(32))
```

## Step 3: Deploy Backend

### 3.1 Backend Service Configuration

1. If deploying from GitHub, Railway will auto-detect and deploy
2. If manual deployment:
   - Select "Deploy from GitHub" → select your repository
   - Railway will use `railway.json` configuration

### 3.2 Verify railway.json

Your `railway.json` should contain:

```json
{
  "$schema": "https://railway.com/railway.schema.json",
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "uvicorn app.main:app --host 0.0.0.0 --port $PORT",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

### 3.3 Deploy

- Push to GitHub (Railway auto-deploys)
- Or click "Deploy" in Railway dashboard

## Step 4: Initialize Database

After backend is deployed:

### Option A: Using Railway CLI

```bash
railway link  # Connect to your Railway project
railway shell

# Inside the shell:
python -c "
from app.db.database import Base, engine
from app.models import models
Base.metadata.create_all(bind=engine)
"
```

### Option B: Using a Migration Script

Create a migration job in Railway that runs once per deployment:
- Add environment variable: `RUN_MIGRATIONS=true`
- Update start command to check this flag

## Step 5: Deploy Frontend

### 5.1 Build Frontend for Production

Create a new Railway service for the frontend:

1. Click "+ New Service" in your Railway project
2. Select "Build from GitHub" 
3. Point to your repository
4. Set the following configuration:

**Service Name:** F1-API-Frontend (or your choice)

**Root Directory:** `frontend`

### 5.2 Environment Variables for Frontend Build

Add these environment variables for the frontend build:

```
VITE_API_URL=https://your-backend-api-url.railway.app
```

Replace `your-backend-api-url` with your actual backend Railway domain.

### 5.3 Build & Start Commands

Set these in Railway deployment settings:

**Build Command:**
```bash
npm install && npm run build
```

**Start Command:**
```bash
npm run preview
```

Or use a static hosting option if available.

## Step 6: Connect Frontend to Backend

The frontend will automatically use the `VITE_API_URL` environment variable set in Railway. 

If not set, the frontend will try to use the same domain as the app is running on, which works if both frontend and backend are served from the same domain.

## Step 7: Custom Domain (Optional)

1. Go to your Railway project
2. Click on the backend service
3. Go to "Settings" → "Domain"
4. Click "Add Domain" and enter your custom domain (e.g., `api.yourdomain.com`)
5. Follow DNS configuration instructions

For frontend, do the same if you want it on a separate domain.

## Step 8: Verify Deployment

### 8.1 Check Backend Health

```bash
curl https://your-backend-url/

# Expected response:
# {"message": "F1 API is running"}
```

### 8.2 Check Swagger Documentation

Visit: `https://your-backend-url/docs`

### 8.3 Check Frontend

Visit your frontend URL in browser

## Troubleshooting

### Database Connection Issues

1. Check `DATABASE_URL` is correctly set in Railway
2. Verify PostgreSQL service is running
3. Check logs: Railway Dashboard → Service → Logs

### CORS Issues

If frontend gets CORS errors:
1. Update `ALLOWED_ORIGINS` to include your frontend domain
2. Redeploy backend
3. Check browser console for exact error

### Frontend Not Loading

1. Check `VITE_API_URL` is correct
2. Verify frontend build succeeded (check Logs)
3. Clear browser cache and hard refresh

### Admin Login Not Working

1. Verify `ADMIN_USERNAME` and `ADMIN_PASSWORD` are set in Railway
2. Use correct credentials in login page
3. Check backend logs for auth errors

## Environment Variable Reference

| Variable | Purpose | Example |
|----------|---------|---------|
| `DATABASE_URL` | PostgreSQL connection | Auto-set by Railway |
| `SECRET_KEY` | JWT signing key | `abc123...` |
| `ADMIN_USERNAME` | Admin login email | `admin@gmail.com` |
| `ADMIN_PASSWORD` | Admin login password | `secure123!` |
| `ALLOWED_ORIGINS` | CORS allowed domains | `https://yourdomain.com` |
| `VITE_API_URL` | Frontend API endpoint | `https://api.yourdomain.com` |
| `PORT` | Backend port | `8000` (auto-set) |

## Maintenance

### Updating Dependencies

```bash
# Backend
pip install --upgrade pip
pip install -r requirements.txt

# Frontend
npm update
```

### Backup Database

Railway provides automatic backups. To manually export:

```bash
railway link
railway shell
pg_dump $DATABASE_URL > backup.sql
```

### View Logs

In Railway Dashboard:
1. Select your service
2. Click "Logs" tab
3. Filter by date/severity as needed

## Additional Resources

- [Railway Docs](https://docs.railway.app)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)
- [Vite Production Build](https://vitejs.dev/guide/build.html)
- [PostgreSQL on Railway](https://docs.railway.app/guides/databases)

## Support

If you encounter issues:
1. Check Railway status page: https://status.railway.app
2. Review service logs in Railway dashboard
3. Check GitHub issues in your repository
4. Contact Railway support for platform-specific issues
