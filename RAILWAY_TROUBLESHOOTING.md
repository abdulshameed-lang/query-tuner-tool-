# 🔧 Railway Deployment Troubleshooting

Your backend URL returns "Application not found" which means the FastAPI app isn't starting.

---

## ✅ Quick Fix Steps

### Step 1: Check Railway Logs

1. Go to https://railway.app/dashboard
2. Click on your service: `query-tuner-backend-production`
3. Click "Deployments" tab
4. Click the latest deployment
5. Read the logs - look for error messages

**Common errors:**
- `ModuleNotFoundError` - Missing dependency
- `ImportError` - Import path issues
- `DatabaseError` - Database connection issues
- `Port binding error` - Port configuration issues

---

### Step 2: Trigger Redeploy (with latest fixes)

I just pushed a database configuration fix. Redeploy to get it:

1. In Railway dashboard, go to your service
2. Click "Deployments"
3. Click the three dots menu
4. Select "Redeploy"

Or trigger from GitHub:
```bash
# Make a small change to trigger rebuild
cd /Users/abdul/dev/query_tuner_tool
git commit --allow-empty -m "trigger railway redeploy"
git push origin main
```

---

### Step 3: Verify Environment Variables

In Railway dashboard, click on your service → "Variables" tab.

**Required variables:**

```bash
# CRITICAL - Add these if missing:
PORT=8000
ENVIRONMENT=production
SECRET_KEY=your-super-secret-key-change-this-to-something-random
JWT_SECRET=another-secret-key-for-jwt-tokens

# IMPORTANT - Add frontend URL to CORS:
CORS_ORIGINS=["https://rare-it-querytime.vercel.app"]

# OPTIONAL - If using custom domain for backend:
ALLOWED_HOSTS=["query-tuner-backend-production.up.railway.app"]

# Database (default is fine):
DATABASE_URL=sqlite:///./query_tuner.db
```

**How to add:**
1. Click "Variables" tab
2. Click "New Variable"
3. Enter name and value
4. Click "Add"
5. Repeat for each variable

---

### Step 4: Verify Build Configuration

Check Railway service settings:

1. Go to your service → "Settings"
2. Verify:
   - **Root Directory:** `/backend` (or blank if root)
   - **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Build Command:** (leave blank - uses requirements.txt automatically)

If Root Directory is blank, the start command should be:
```
cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

---

### Step 5: Check Requirements File

Railway should be using `/backend/requirements.txt` which has simplified dependencies (no Oracle).

Verify this file exists and has correct content:
```bash
cat /Users/abdul/dev/query_tuner_tool/backend/requirements.txt
```

Should contain:
- fastapi
- uvicorn
- pydantic
- sqlalchemy
- python-jose
- passlib
- httpx
- python-dotenv

---

## 🔍 Debugging Specific Errors

### Error: "ModuleNotFoundError: No module named 'app'"

**Fix:** Check Root Directory setting
- If Root Directory = `/backend`, start command should be:
  ```
  uvicorn app.main:app --host 0.0.0.0 --port $PORT
  ```
- If Root Directory = blank (root of repo), start command should be:
  ```
  cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT
  ```

### Error: "No module named 'redis'"

**Cause:** requirements.txt includes redis but it's not in simplified version

**Fix:** Either:
1. **Option A:** Remove redis dependency (recommended for now)
   ```bash
   # Edit backend/requirements.txt and remove redis line
   # Then git commit and push
   ```

2. **Option B:** Add redis service in Railway
   - Add new service → Database → Redis
   - Copy REDIS_URL
   - Add as environment variable

### Error: "Address already in use"

**Fix:** Make sure PORT environment variable is set to `$PORT` (Railway's dynamic port)

### Error: Database connection failed

**Fix:** SQLite should work. Make sure:
```
DATABASE_URL=sqlite:///./query_tuner.db
```

---

## 🧪 Test After Fix

Once redeployed, test these endpoints:

```bash
# Health check
curl https://query-tuner-backend-production.up.railway.app/health

# API root
curl https://query-tuner-backend-production.up.railway.app/

# API v1
curl https://query-tuner-backend-production.up.railway.app/api/v1/

# Auth endpoints (should return method not allowed, not 404)
curl https://query-tuner-backend-production.up.railway.app/api/v1/auth/signup
```

**Expected responses:**
- `/health` → `{"status":"healthy",...}`
- `/` → `{"name":"Oracle Query Tuner API",...}`
- `/api/v1/` → `{"message":"Query Tuner API v1",...}`
- `/api/v1/auth/signup` → `{"detail":"Method Not Allowed"}` (405 is good! means endpoint exists)

---

## 📋 Checklist

After fixing, verify:
- [ ] Railway deployment shows "Active" status (green)
- [ ] No errors in deployment logs
- [ ] `/health` endpoint returns 200
- [ ] `/` returns FastAPI app info
- [ ] `/api/v1/` returns API info
- [ ] Environment variables are set correctly

---

## 🆘 Still Not Working?

### Share These Details:

1. **Railway deployment logs** (last 50 lines)
2. **Environment variables** (names only, not values)
3. **Service settings:**
   - Root Directory
   - Start Command
   - Build Command

### Quick Test Locally:

```bash
cd /Users/abdul/dev/query_tuner_tool/backend

# Set environment
export ENVIRONMENT=production
export SECRET_KEY=test-secret
export DATABASE_URL=sqlite:///./test.db

# Install dependencies
pip install -r requirements.txt

# Run
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

If it works locally but not on Railway, it's a Railway configuration issue.

---

## 📞 Next Steps

Once Railway shows your app running:

1. Test the URL works: `https://query-tuner-backend-production.up.railway.app/health`
2. Let me know - I'll finalize the frontend configuration
3. Deploy frontend to Vercel
4. Test the full application

---

**Check Railway logs now and let me know what error you see!** 🔍
