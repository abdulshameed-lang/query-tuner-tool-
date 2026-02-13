# Deployment Guide - RARE-IT QueryTune Pro

Deploy the application to **https://rare-it.querytune.com**

---

## 🚀 Quick Deployment Steps

### Step 1: Build Frontend for Production

```bash
cd /Users/abdul/dev/query_tuner_tool/frontend

# Install dependencies (if not already done)
npm install

# Build for production
npm run build
```

This creates an optimized production build in `frontend/dist/`

**Output:**
```
frontend/dist/
├── index.html
├── assets/
│   ├── index-[hash].js
│   ├── index-[hash].css
│   └── [other assets]
└── vite.svg
```

---

### Step 2: Configure Environment Variables

Create `.env.production` in frontend directory:

```bash
cat > /Users/abdul/dev/query_tuner_tool/frontend/.env.production << 'EOF'
VITE_API_URL=https://api.rare-it.querytune.com
VITE_APP_URL=https://rare-it.querytune.com
EOF
```

**If backend is on same domain:**
```bash
VITE_API_URL=https://rare-it.querytune.com/api
```

---

### Step 3: Deploy Frontend

#### Option A: Deploy to Static Hosting (Recommended)

**Vercel (Easiest):**
```bash
# Install Vercel CLI
npm install -g vercel

# Deploy
cd /Users/abdul/dev/query_tuner_tool/frontend
vercel --prod
```

**Netlify:**
```bash
# Install Netlify CLI
npm install -g netlify-cli

# Deploy
cd /Users/abdul/dev/query_tuner_tool/frontend
netlify deploy --prod --dir=dist
```

**Configure SPA routing:**
Create `frontend/dist/_redirects` (for Netlify):
```
/*    /index.html   200
```

Or `vercel.json` (for Vercel):
```json
{
  "rewrites": [
    { "source": "/(.*)", "destination": "/index.html" }
  ]
}
```

---

#### Option B: Deploy to Your Own Server (Nginx)

**1. Upload files to server:**
```bash
# Copy dist folder to server
scp -r frontend/dist/* user@rare-it.querytune.com:/var/www/rare-it.querytune.com/
```

**2. Configure Nginx:**

Create `/etc/nginx/sites-available/rare-it.querytune.com`:

```nginx
server {
    listen 80;
    server_name rare-it.querytune.com www.rare-it.querytune.com;

    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name rare-it.querytune.com www.rare-it.querytune.com;

    # SSL Certificate
    ssl_certificate /etc/letsencrypt/live/rare-it.querytune.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/rare-it.querytune.com/privkey.pem;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Root directory
    root /var/www/rare-it.querytune.com;
    index index.html;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1000;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;

    # SPA routing - serve index.html for all routes
    location / {
        try_files $uri $uri/ /index.html;
    }

    # API proxy (if backend is separate)
    location /api {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Cache static assets
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

**3. Enable site and reload Nginx:**
```bash
sudo ln -s /etc/nginx/sites-available/rare-it.querytune.com /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

#### Option C: Deploy to Apache

Create `/etc/apache2/sites-available/rare-it.querytune.com.conf`:

```apache
<VirtualHost *:80>
    ServerName rare-it.querytune.com
    ServerAlias www.rare-it.querytune.com

    RewriteEngine On
    RewriteCond %{HTTPS} off
    RewriteRule ^(.*)$ https://%{HTTP_HOST}%{REQUEST_URI} [L,R=301]
</VirtualHost>

<VirtualHost *:443>
    ServerName rare-it.querytune.com
    ServerAlias www.rare-it.querytune.com

    DocumentRoot /var/www/rare-it.querytune.com

    SSLEngine on
    SSLCertificateFile /etc/letsencrypt/live/rare-it.querytune.com/fullchain.pem
    SSLCertificateKeyFile /etc/letsencrypt/live/rare-it.querytune.com/privkey.pem

    <Directory /var/www/rare-it.querytune.com>
        Options -Indexes +FollowSymLinks
        AllowOverride All
        Require all granted

        # SPA routing
        RewriteEngine On
        RewriteBase /
        RewriteRule ^index\.html$ - [L]
        RewriteCond %{REQUEST_FILENAME} !-f
        RewriteCond %{REQUEST_FILENAME} !-d
        RewriteRule . /index.html [L]
    </Directory>

    # Proxy API requests
    ProxyPass /api http://localhost:8000
    ProxyPassReverse /api http://localhost:8000
</VirtualHost>
```

**Enable and restart:**
```bash
sudo a2ensite rare-it.querytune.com
sudo a2enmod rewrite ssl proxy proxy_http
sudo systemctl restart apache2
```

---

### Step 4: Setup SSL Certificate (HTTPS)

**Using Let's Encrypt (Free):**

```bash
# Install Certbot
sudo apt-get update
sudo apt-get install certbot python3-certbot-nginx

# For Nginx
sudo certbot --nginx -d rare-it.querytune.com -d www.rare-it.querytune.com

# For Apache
sudo certbot --apache -d rare-it.querytune.com -d www.rare-it.querytune.com

# Auto-renewal (already set up by certbot)
sudo certbot renew --dry-run
```

---

### Step 5: Deploy Backend API

**Option A: Same Server with Frontend**

```bash
# 1. Copy backend files
scp -r backend/ user@rare-it.querytune.com:/opt/querytune/

# 2. On server, install dependencies
cd /opt/querytune/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements/prod.txt

# 3. Create systemd service
sudo nano /etc/systemd/system/querytune-api.service
```

**Service file:**
```ini
[Unit]
Description=QueryTune API
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/querytune/backend
Environment="PATH=/opt/querytune/backend/venv/bin"
ExecStart=/opt/querytune/backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always

[Install]
WantedBy=multi-user.target
```

**Start service:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable querytune-api
sudo systemctl start querytune-api
sudo systemctl status querytune-api
```

---

**Option B: Separate API Subdomain**

Deploy backend to `api.rare-it.querytune.com`:

1. Point DNS A record: `api.rare-it.querytune.com` → Server IP
2. Configure Nginx for API:

```nginx
server {
    listen 443 ssl http2;
    server_name api.rare-it.querytune.com;

    ssl_certificate /etc/letsencrypt/live/api.rare-it.querytune.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.rare-it.querytune.com/privkey.pem;

    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # CORS headers
        add_header Access-Control-Allow-Origin "https://rare-it.querytune.com" always;
        add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS" always;
        add_header Access-Control-Allow-Headers "Authorization, Content-Type" always;
    }
}
```

---

### Step 6: Configure DNS

Point your domain to the server:

```
A Record:
  Host: rare-it.querytune.com
  Points to: YOUR_SERVER_IP
  TTL: 3600

A Record (for www):
  Host: www.rare-it.querytune.com
  Points to: YOUR_SERVER_IP
  TTL: 3600

CNAME (if using API subdomain):
  Host: api.rare-it.querytune.com
  Points to: rare-it.querytune.com
  TTL: 3600
```

---

## 🔧 Update Frontend API Configuration

Before building, update the API client:

Edit `frontend/src/services/apiClient.ts`:

```typescript
const API_BASE_URL = import.meta.env.VITE_API_URL ||
  (import.meta.env.PROD
    ? 'https://rare-it.querytune.com/api'  // Production API
    : 'http://localhost:8000/api/v1'        // Development API
  );
```

---

## 📦 Build and Deploy Script

Create `deploy.sh` in project root:

```bash
#!/bin/bash

echo "🚀 Building and deploying RARE-IT QueryTune Pro..."

# Build frontend
cd frontend
echo "📦 Building frontend..."
npm run build

# Deploy to server (adjust to your method)
echo "🌐 Deploying to rare-it.querytune.com..."
rsync -avz --delete dist/ user@rare-it.querytune.com:/var/www/rare-it.querytune.com/

# Restart backend (if needed)
echo "🔄 Restarting backend..."
ssh user@rare-it.querytune.com "sudo systemctl restart querytune-api"

echo "✅ Deployment complete!"
echo "🌍 Visit: https://rare-it.querytune.com"
```

Make executable and run:
```bash
chmod +x deploy.sh
./deploy.sh
```

---

## 🧪 Testing After Deployment

1. **Test Landing Page:**
   ```
   https://rare-it.querytune.com
   ```
   Should show RARE-IT branded landing page

2. **Test Login:**
   ```
   https://rare-it.querytune.com/login
   ```

3. **Test API:**
   ```bash
   curl https://rare-it.querytune.com/api/health
   # or
   curl https://api.rare-it.querytune.com/health
   ```

4. **Test Protected Routes:**
   - Login with credentials
   - Navigate to: `https://rare-it.querytune.com/app`
   - Should see dashboard

---

## 🔒 Security Checklist

- ✅ HTTPS enabled (SSL certificate)
- ✅ HTTP → HTTPS redirect
- ✅ Security headers configured
- ✅ CORS properly configured
- ✅ Firewall rules set (allow 80, 443)
- ✅ Database credentials secured
- ✅ Environment variables protected
- ✅ Regular backups configured

---

## 🐛 Troubleshooting

**Issue: "Cannot GET /" or 404 on routes**
- Solution: Ensure SPA routing is configured (try_files in Nginx or RewriteRule in Apache)

**Issue: API calls fail (CORS errors)**
- Solution: Check CORS configuration in backend and Nginx/Apache proxy

**Issue: Blank page after deployment**
- Solution: Check browser console for errors, verify API_BASE_URL is correct

**Issue: SSL certificate errors**
- Solution: Run `sudo certbot renew`, check certificate paths in Nginx/Apache

**Issue: Backend not responding**
- Solution: Check service status: `sudo systemctl status querytune-api`
- Check logs: `sudo journalctl -u querytune-api -f`

---

## 📊 Monitoring

Set up monitoring for production:

1. **Uptime Monitoring:**
   - UptimeRobot, Pingdom, or StatusCake
   - Monitor: https://rare-it.querytune.com

2. **Server Monitoring:**
   - Install: htop, netdata, or Grafana
   - Monitor: CPU, Memory, Disk, Network

3. **Application Logs:**
   ```bash
   # Nginx logs
   tail -f /var/log/nginx/access.log
   tail -f /var/log/nginx/error.log

   # Backend logs
   sudo journalctl -u querytune-api -f
   ```

---

## 🔄 CI/CD (Optional)

**GitHub Actions** for automatic deployment:

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v2

      - name: Setup Node.js
        uses: actions/setup-node@v2
        with:
          node-version: '18'

      - name: Build Frontend
        run: |
          cd frontend
          npm install
          npm run build

      - name: Deploy to Server
        uses: appleboy/scp-action@master
        with:
          host: ${{ secrets.SERVER_HOST }}
          username: ${{ secrets.SERVER_USER }}
          key: ${{ secrets.SSH_KEY }}
          source: "frontend/dist/*"
          target: "/var/www/rare-it.querytune.com/"
```

---

## 🎉 Quick Start (If You Have Server Access)

```bash
# 1. Build frontend
cd /Users/abdul/dev/query_tuner_tool/frontend
npm run build

# 2. Copy to server
scp -r dist/* user@your-server:/var/www/rare-it.querytune.com/

# 3. Configure Nginx (use config above)
# 4. Setup SSL with Certbot
# 5. Deploy backend as systemd service

# Done! Access at https://rare-it.querytune.com
```

---

**Need help with deployment? Let me know:**
- What hosting provider are you using?
- Do you have server access (VPS, dedicated)?
- Or using static hosting (Vercel, Netlify)?

**Last Updated:** February 12, 2026
