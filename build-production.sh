#!/bin/bash

echo "🚀 Building RARE-IT QueryTune Pro for Production..."
echo ""

# Navigate to frontend
cd "$(dirname "$0")/frontend"

# Install dependencies
echo "📦 Installing dependencies..."
npm install

# Build for production
echo "🔨 Building production bundle..."
npm run build

# Check if build was successful
if [ -d "dist" ]; then
    echo ""
    echo "✅ Build successful!"
    echo ""
    echo "📂 Production files are in: frontend/dist/"
    echo ""
    echo "📊 Build size:"
    du -sh dist/
    echo ""
    echo "📝 Next steps:"
    echo "1. Upload dist/ folder to your web server"
    echo "2. Configure Nginx or Apache (see DEPLOYMENT_GUIDE.md)"
    echo "3. Setup SSL certificate with Let's Encrypt"
    echo "4. Point DNS to your server"
    echo ""
    echo "🌍 Your site will be available at: https://rare-it.querytune.com"
else
    echo ""
    echo "❌ Build failed!"
    echo "Check the errors above and try again."
    exit 1
fi
