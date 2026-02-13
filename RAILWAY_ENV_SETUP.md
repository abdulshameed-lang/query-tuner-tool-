# Railway Environment Variables Setup

## 🚨 Your app is crashing because of missing environment variables!

---

## ✅ Required Variables - Add These in Railway NOW

Go to Railway Dashboard → Your Service → **Variables** tab → Click "Raw Editor"

**Paste this entire configuration:**

```bash
ENVIRONMENT=production
PORT=8000
SECRET_KEY=super-secret-key-change-this-to-something-random-and-long-32chars
JWT_SECRET=jwt-secret-key-also-change-this-to-something-random-32chars
DATABASE_URL=sqlite:///./query_tuner.db
CORS_ORIGINS=["https://rare-it-querytime.vercel.app"]
ALLOWED_HOSTS=["query-tuner-backend-production.up.railway.app"]
LOG_LEVEL=INFO
DEBUG=false
```

---

## 📋 Step-by-Step Instructions

### Option 1: Raw Editor (Fastest)

1. Go to Railway dashboard
2. Click your service: `query-tuner-backend-production`
3. Click "Variables" tab
4. Click **"Raw Editor"** button
5. **Delete everything** in the editor
6. **Paste the configuration above**
7. Click "Save"
8. Railway will automatically redeploy

### Option 2: Add One by One

Click "New Variable" and add each one:

| Variable | Value |
|----------|-------|
| `ENVIRONMENT` | `production` |
| `PORT` | `8000` |
| `SECRET_KEY` | `your-random-secret-at-least-32-characters-long` |
| `JWT_SECRET` | `your-jwt-secret-at-least-32-characters-long` |
| `DATABASE_URL` | `sqlite:///./query_tuner.db` |
| `CORS_ORIGINS` | `["https://rare-it-querytime.vercel.app"]` |
| `ALLOWED_HOSTS` | `["query-tuner-backend-production.up.railway.app"]` |
| `LOG_LEVEL` | `INFO` |
| `DEBUG` | `false` |

---

## 🔑 Generate Secure Secret Keys

**For SECRET_KEY and JWT_SECRET, use random strings:**

```bash
# Run this in your terminal to generate random keys:
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

Run it twice, use first output for SECRET_KEY, second for JWT_SECRET.

Or use any random string at least 32 characters long.

---

## ⚠️ Important Notes

### CORS_ORIGINS Format

Must be a JSON array with quotes:
```
CORS_ORIGINS=["https://rare-it-querytime.vercel.app"]
```

NOT:
```
CORS_ORIGINS=https://rare-it-querytime.vercel.app  ❌
```

### ALLOWED_HOSTS Format

Also a JSON array:
```
ALLOWED_HOSTS=["query-tuner-backend-production.up.railway.app"]
```

---

## 🧪 After Setting Variables

1. Railway will automatically redeploy (takes 2-3 minutes)
2. Check "Deployments" tab - wait for "Active" status
3. Test: https://query-tuner-backend-production.up.railway.app/health
4. Should see: `{"status":"healthy","environment":"production"}`

---

## 🔍 If Still Crashing

Check the **runtime logs** (not build logs):

1. Go to Deployments tab
2. Click latest deployment
3. Look at logs section
4. Find the error message (usually at the end)
5. Share it with me

---

## 📞 Common Crash Causes

| Error | Cause | Fix |
|-------|-------|-----|
| `KeyError: 'SECRET_KEY'` | Missing SECRET_KEY | Add SECRET_KEY variable |
| `KeyError: 'CORS_ORIGINS'` | Missing or wrong format | Use JSON array format |
| `ModuleNotFoundError` | Missing dependency | Check requirements.txt |
| `Port already in use` | Wrong PORT variable | Use `PORT=8000` |
| `Database connection failed` | Wrong DATABASE_URL | Use `sqlite:///./query_tuner.db` |

---

**Set these variables now and wait for Railway to redeploy!** ⚡
