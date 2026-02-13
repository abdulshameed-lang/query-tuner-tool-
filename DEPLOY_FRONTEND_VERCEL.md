# Deploy Frontend to Vercel - Complete Guide

## Prerequisites

✅ Backend deployed to Railway (get the URL first)
✅ Railway backend URL (e.g., `https://your-app.up.railway.app`)

---

## Step 1: Update Environment Variables

Once you have your Railway backend URL, update the production environment file:

```bash
# Edit this file
nano /Users/abdul/dev/query_tuner_tool/frontend/.env.production
```

Replace `YOUR-RAILWAY-APP` with your actual Railway URL:

```env
VITE_API_URL=https://your-actual-railway-app.up.railway.app/api/v1
VITE_APP_NAME=RARE-IT QueryTune Pro
VITE_ENVIRONMENT=production
```

**Example:**
```env
VITE_API_URL=https://query-tuner-backend-production.up.railway.app/api/v1
```

---

## Step 2: Test Build Locally (Optional but Recommended)

```bash
cd /Users/abdul/dev/query_tuner_tool/frontend

# Install dependencies if needed
npm install

# Build for production
npm run build

# Preview the build
npm run preview
```

This ensures the build works before deploying to Vercel.

---

## Step 3: Deploy to Vercel

### Option A: Using Vercel CLI (Recommended)

```bash
cd /Users/abdul/dev/query_tuner_tool/frontend

# Install Vercel CLI if not installed
npm install -g vercel

# Login to Vercel (if not already logged in)
vercel login

# Deploy to production
vercel --prod
```

**During deployment, Vercel will ask:**
- Project name: `rare-it-querytime` (or your preference)
- Framework: `Vite` (auto-detected)
- Build command: `npm run build`
- Output directory: `dist`

### Option B: Using Vercel Dashboard

1. Go to https://vercel.com/dashboard
2. Click "Add New" → "Project"
3. Import your GitHub repository: `query-tuner-tool-`
4. Configure:
   - **Root Directory:** `frontend`
   - **Framework Preset:** Vite
   - **Build Command:** `npm run build`
   - **Output Directory:** `dist`
5. Add Environment Variables:
   - `VITE_API_URL` = `https://your-railway-app.up.railway.app/api/v1`
   - `VITE_APP_NAME` = `RARE-IT QueryTune Pro`
   - `VITE_ENVIRONMENT` = `production`
6. Click "Deploy"

---

## Step 4: Set Environment Variables in Vercel (CLI Method)

If using Vercel CLI, set environment variables after first deployment:

```bash
# Set production environment variables
vercel env add VITE_API_URL production
# When prompted, enter: https://your-railway-app.up.railway.app/api/v1

vercel env add VITE_APP_NAME production
# When prompted, enter: RARE-IT QueryTune Pro

vercel env add VITE_ENVIRONMENT production
# When prompted, enter: production

# Redeploy to apply environment variables
vercel --prod
```

---

## Step 5: Verify Deployment

After deployment completes, you'll get a URL like:
```
https://rare-it-querytime.vercel.app
```

### Test the following:

1. **Frontend loads:** Open https://rare-it-querytime.vercel.app
2. **API connection:** Check browser console (should show API URL)
3. **Sign Up:** Create a new account
4. **Login:** Login with the account
5. **Features:** Test dashboard and features

### Debugging:

If the app doesn't work:

1. **Check Browser Console:**
   - Look for API URL log: `API URL configured: https://...`
   - Check for CORS errors
   - Check for 404 or 500 errors

2. **Check Railway Backend:**
   - Is it running? Check Railway dashboard
   - Check Railway logs for errors
   - Test API endpoint: `https://your-railway-app.up.railway.app/api/v1/health`

3. **Check Environment Variables in Vercel:**
   - Go to Vercel Dashboard → Your Project → Settings → Environment Variables
   - Verify `VITE_API_URL` is correct

---

## Step 6: Configure Custom Domain (Optional)

If you want to use `rare-it.querytune.com`:

1. Go to Vercel Dashboard → Your Project → Settings → Domains
2. Add domain: `rare-it.querytune.com`
3. Follow Vercel's DNS configuration instructions
4. Update your DNS provider with Vercel's records

---

## Quick Reference Commands

```bash
# Deploy to production
cd /Users/abdul/dev/query_tuner_tool/frontend
vercel --prod

# Check deployment status
vercel ls

# View logs
vercel logs

# Remove deployment
vercel remove [deployment-url]
```

---

## Troubleshooting

### Issue: "API URL configured: http://localhost:8000/api/v1" in production

**Solution:** Environment variable not set correctly.

```bash
# Check if .env.production exists
cat /Users/abdul/dev/query_tuner_tool/frontend/.env.production

# Verify environment variables in Vercel
vercel env ls

# Re-add if missing
vercel env add VITE_API_URL production
```

### Issue: CORS errors in browser console

**Solution:** Backend needs to allow Vercel domain.

Check Railway backend environment variables include:
```
CORS_ORIGINS=https://rare-it-querytime.vercel.app,https://rare-it.querytune.com
```

### Issue: 404 on page refresh

**Solution:** Already configured in `vercel.json` - should work automatically.

If not, verify `vercel.json` exists with:
```json
{
  "rewrites": [
    { "source": "/(.*)", "destination": "/index.html" }
  ]
}
```

---

## Post-Deployment Checklist

- [ ] Frontend loads at Vercel URL
- [ ] API URL is correct (check console)
- [ ] Sign up works
- [ ] Login works
- [ ] Dashboard loads
- [ ] No CORS errors
- [ ] No 404 errors on refresh

---

## Success! 🎉

Your application should now be fully deployed:

- **Frontend:** https://rare-it-querytime.vercel.app
- **Backend:** https://your-railway-app.up.railway.app
- **Status:** Fully functional online!

---

**Next Steps:**

1. Test all features thoroughly
2. Monitor Railway and Vercel logs
3. Set up custom domain (optional)
4. Configure monitoring and alerts (optional)
