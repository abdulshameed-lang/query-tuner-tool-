#!/bin/bash

echo "🚀 Deploying RARE-IT QueryTune Pro to Vercel..."
echo ""

cd "$(dirname "$0")/frontend"

# Check if logged in to Vercel
if ! vercel whoami > /dev/null 2>&1; then
    echo "🔐 Please login to Vercel..."
    vercel login
fi

echo ""
echo "📦 Deploying production build..."
echo ""

# Deploy to production
vercel --prod

echo ""
echo "✅ Deployment complete!"
echo ""
echo "📝 Next steps:"
echo "1. Go to https://vercel.com/dashboard"
echo "2. Select your project"
echo "3. Go to Settings > Domains"
echo "4. Add custom domain: rare-it.querytune.com"
echo "5. Follow Vercel's DNS configuration instructions"
echo ""
