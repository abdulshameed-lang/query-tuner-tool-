#!/bin/bash

# Script to update Railway backend URL in frontend configuration

echo "=================================================="
echo "Update Frontend with Railway Backend URL"
echo "=================================================="
echo ""

# Get Railway URL from user
echo "Enter your Railway backend URL (without /api/v1):"
echo "Example: https://query-tuner-backend-production.up.railway.app"
read -p "Railway URL: " RAILWAY_URL

# Validate URL
if [[ ! $RAILWAY_URL =~ ^https:// ]]; then
    echo "❌ Error: URL must start with https://"
    exit 1
fi

# Remove trailing slash if present
RAILWAY_URL=${RAILWAY_URL%/}

echo ""
echo "Updating configuration..."

# Update .env.production
cat > frontend/.env.production << EOF
# Production environment variables
VITE_API_URL=${RAILWAY_URL}/api/v1
VITE_APP_NAME=RARE-IT QueryTune Pro
VITE_ENVIRONMENT=production
EOF

echo "✅ Updated frontend/.env.production"

# Display the configuration
echo ""
echo "=================================================="
echo "Configuration Updated!"
echo "=================================================="
echo "API URL: ${RAILWAY_URL}/api/v1"
echo ""
echo "Next steps:"
echo "1. Test locally: cd frontend && npm run build && npm run preview"
echo "2. Deploy to Vercel: cd frontend && vercel --prod"
echo ""
echo "Or set environment variable in Vercel:"
echo "   vercel env add VITE_API_URL production"
echo "   Value: ${RAILWAY_URL}/api/v1"
echo "=================================================="
