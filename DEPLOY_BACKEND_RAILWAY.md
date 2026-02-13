# Deploy Backend to Railway - Step by Step

This will make your application fully functional online!

---

## 🚀 Quick Deploy (15 minutes)

### Step 1: Push Code to GitHub

```bash
cd /Users/abdul/dev/query_tuner_tool

# Initialize git if not done
git init

# Add all files
git add .

# Commit
git commit -m "Prepare for Railway deployment"

# Create GitHub repo and push
# Go to: https://github.com/new
# Create repository named: query-tuner-tool
# Then run:

git remote add origin https://github.com/YOUR_USERNAME/query-tuner-tool.git
git branch -M main
git push -u origin main
```

---

### Step 2: Deploy to Railway

1. **Go to Railway:**
   ```
   https://railway.app
   ```

2. **Login with GitHub**
   - Click "Login"
   - Choose "Login with GitHub"
   - Authorize Railway

3. **Create New Project:**
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose: `query-tuner-tool`

4. **Configure Deployment:**
   - Railway will auto-detect Python
   - Root Directory: `/backend`
   - Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

5. **Add Environment Variables:**
   Click "Variables" and add:
   ```
   PORT=8000
   DATABASE_URL=sqlite:///./query_tuner.db
   SECRET_KEY=your-secret-key-here-change-this
   ```

6. **Deploy!**
   - Click "Deploy"
   - Wait 2-3 minutes
   - You'll get a URL like: `https://query-tuner-backend.up.railway.app`

---

### Step 3: Update Frontend to Use Railway Backend

Update the API URL in frontend to point to Railway:

**Backend URL from Railway:**
```
https://YOUR-APP-NAME.up.railway.app
```

Then redeploy frontend to Vercel.

---

## ✅ After Deployment

Your application will be fully functional:
- ✅ Frontend: https://rare-it-querytime.vercel.app
- ✅ Backend: https://your-app.up.railway.app
- ✅ Signup works
- ✅ Login works
- ✅ All features work

---

**Follow these steps and let me know when you get stuck!** 🚀
