#!/bin/bash
# CampusIQ Production Build Script
# This script builds the frontend and prepares for single-server deployment

echo "🚀 Building CampusIQ for Production..."
echo ""

# Step 1: Build Frontend
echo "📦 Building Frontend..."
cd frontend
if [ -d "dist" ]; then
    rm -rf dist
    echo "✓ Cleaned previous build"
fi
npm install
npm run build
echo "✓ Frontend built successfully"
echo ""

# Step 2: Verify build output
cd ..
if [ -f "frontend/dist/index.html" ]; then
    echo "✓ Build verification passed"
else
    echo "✗ Build verification failed - index.html not found"
    exit 1
fi
echo ""

# Step 3: Display next steps
echo "✅ Production build complete!"
echo ""
echo "Next steps:"
echo "1. cd backend"
echo "2. pip install -r requirements.txt"
echo "3. python -m app.seed_db (if needed)"
echo "4. uvicorn app.main:app --host 0.0.0.0 --port 8000"
echo ""
echo "Or use Docker:"
echo "docker-compose -f docker-compose.production.yml up --build"
echo ""
