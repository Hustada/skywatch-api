# SkyWatch Domain Setup Reference

## 🌐 Domain Strategy

### **Root Domain Purchase**
- **Buy:** `skywatch.dev` (root domain only)
- **Cost:** ~$12-15/year for .dev domain
- **Includes:** Unlimited subdomains automatically

### **Domain Architecture**

```
skywatch.dev                    → Main website/landing page (future)
api.skywatch.dev               → SkyWatch API (current project)
├── /docs                      → API documentation interface
├── /map                       → Interactive UFO sightings map
├── /v1/sightings             → UFO data API endpoints
├── /v1/auth                  → Authentication system
├── /v1/research              → AI research functionality
└── /health                   → API health check

www.skywatch.dev               → Redirect to skywatch.dev
```

### **Current Implementation**
All functionality is served from a **single FastAPI application** at `api.skywatch.dev`:

- ✅ **API Documentation:** `api.skywatch.dev/docs`
- ✅ **Interactive Map:** `api.skywatch.dev/map` 
- ✅ **UFO Data API:** `api.skywatch.dev/v1/sightings`
- ✅ **AI Research:** `api.skywatch.dev/v1/research`
- ✅ **Authentication:** `api.skywatch.dev/v1/auth`

## 🚀 Setup Steps

### 1. Domain Purchase
1. Buy `skywatch.dev` from registrar (Namecheap, GoDaddy, etc.)
2. Access DNS management panel

### 2. DNS Configuration
Add these DNS records:
```
Type: CNAME
Name: api
Value: cname.vercel-dns.com
```

### 3. Vercel Configuration
1. Go to Vercel project settings
2. Add custom domain: `api.skywatch.dev`
3. Vercel will verify DNS and issue SSL certificate

### 4. Environment Variables
Update CORS origins:
```bash
CORS_ORIGINS=https://api.skywatch.dev
```

## 🔮 Future Expansion Options

### **Option A: Keep Everything Together (Recommended)**
```
api.skywatch.dev/docs          → Documentation
api.skywatch.dev/map           → Map interface
api.skywatch.dev/v1/*          → API endpoints
```

**Pros:**
- Single deployment
- Shared authentication
- Shared database access
- Cost effective
- Simpler maintenance

### **Option B: Split Services (Advanced)**
```
skywatch.dev                   → Marketing website
api.skywatch.dev              → Pure API only
map.skywatch.dev              → Standalone map app
docs.skywatch.dev             → Separate documentation
```

**Pros:**
- Independent scaling
- Technology flexibility
- Clear separation of concerns

**Cons:**
- Multiple deployments
- Cross-origin complexity
- Higher costs
- More maintenance

## 📝 Current Status

- ✅ Code configured for `api.skywatch.dev`
- ✅ Documentation already references correct URLs
- ✅ CORS settings ready for production domain
- ✅ Vercel deployment configuration complete
- ⏳ Waiting for domain purchase and DNS setup

## 🛠️ Migration Notes

When switching from Vercel default domain to custom domain:

1. **No code changes needed** - environment variables handle the switch
2. **SSL automatic** - Vercel provisions SSL certificates
3. **Zero downtime** - Vercel handles the transition smoothly
4. **API keys remain valid** - authentication system unchanged

## 🌟 Benefits of Current Architecture

- **Single Source of Truth:** One codebase, one deployment
- **Shared Resources:** Database, auth, caching all integrated
- **Performance:** No cross-origin API calls for map data
- **SEO Friendly:** All content served from consistent domain
- **Cost Effective:** One hosting plan covers everything

---

**Current URLs in documentation:**
- All examples use `https://api.skywatch.dev`
- Ready for production deployment
- No URL updates needed after domain setup