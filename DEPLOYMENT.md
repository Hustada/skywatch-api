# SkyWatch API - Vercel Deployment Guide

## 📋 Prerequisites
- ✅ Vercel account
- ✅ GitHub repository connected to Vercel
- ✅ Data exported (23.12 MB with 80,317+ UFO sightings)

## 🚀 Deployment Steps

### Step 1: Set up Vercel Postgres Database

1. Go to [Vercel Dashboard](https://vercel.com/dashboard)
2. Navigate to Storage tab
3. Create a new Postgres database
4. Note down the connection details:
   - `POSTGRES_URL`
   - `POSTGRES_PRISMA_URL` 
   - `POSTGRES_URL_NON_POOLING`

### Step 2: Configure Environment Variables

In your Vercel project settings, add these environment variables:

```bash
# Database
DATABASE_URL=<your_postgres_url>

# Security
JWT_SECRET_KEY=<generate_secure_key>
ENVIRONMENT=production

# AI Research
GEMINI_API_KEY=<your_gemini_key>

# CORS (update with your domain)
CORS_ORIGINS=https://your-app.vercel.app,https://api.skywatch.dev
```

**Generate JWT Secret Key:**
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Step 3: Import Database Data

After deployment, run the migration:

```bash
# Test connection first
python migrate_to_postgres.py test "postgresql://user:pass@host:5432/db"

# Import data
python migrate_to_postgres.py import "postgresql://user:pass@host:5432/db"
```

### Step 4: Deploy to Vercel

1. Connect your GitHub repo to Vercel
2. Vercel will auto-detect the FastAPI app
3. Set environment variables in Vercel dashboard
4. Deploy!

## 📁 Files Created for Deployment

- ✅ `vercel.json` - Vercel configuration
- ✅ `migrate_to_postgres.py` - Database migration script  
- ✅ `sightings_export.sql` - Exported data (23.12 MB)
- ✅ Updated `requirements.txt` - Added PostgreSQL drivers
- ✅ Updated `api/database.py` - PostgreSQL support

## 🔧 What's Configured

### API Endpoints (will work at your-app.vercel.app):
- `/docs` - Main documentation interface
- `/v1/sightings` - UFO sightings API
- `/v1/auth` - Authentication system
- `/v1/research` - AI research functionality  
- `/map` - Interactive map interface
- `/health` - Health check

### Features Ready:
- ✅ 80,317+ UFO sightings from NUFORC database
- ✅ AI-powered research with Google Gemini
- ✅ Interactive map with heat map visualization
- ✅ User authentication and API key management
- ✅ Research result caching for performance
- ✅ Professional reference system in reports

## 🌐 Custom Domain (Optional)

To use `api.skywatch.dev`:

1. Add domain in Vercel project settings
2. Update DNS records to point to Vercel
3. Update `CORS_ORIGINS` environment variable

## ⚡ Performance Notes

- PostgreSQL database with connection pooling
- Serverless functions with 30s timeout
- Static files served efficiently
- Research results cached to reduce AI API costs

## 🛠️ Post-Deployment Testing

Test these endpoints after deployment:
- `GET /health` - Should return OK
- `GET /docs` - Main interface should load
- `GET /map` - Map should display with data
- `POST /v1/auth/register` - User registration
- `GET /v1/sightings?limit=10` - Sample data

Your SkyWatch API is ready for production! 🚀