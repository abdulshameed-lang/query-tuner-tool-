#!/bin/bash

# Development startup script for Oracle Query Tuner Tool
# This script starts the backend, frontend, and Redis for testing

set -e

echo "🚀 Starting Oracle Query Tuner Tool - Development Mode"
echo "======================================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if a port is in use
port_in_use() {
    lsof -ti:$1 >/dev/null 2>&1
}

# Check prerequisites
echo "📋 Checking prerequisites..."
echo ""

MISSING_DEPS=0

if ! command_exists python3; then
    echo -e "${RED}❌ Python 3 not found${NC}"
    MISSING_DEPS=1
else
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    echo -e "${GREEN}✅ Python 3 found: $PYTHON_VERSION${NC}"
fi

if ! command_exists node; then
    echo -e "${RED}❌ Node.js not found${NC}"
    MISSING_DEPS=1
else
    NODE_VERSION=$(node --version)
    echo -e "${GREEN}✅ Node.js found: $NODE_VERSION${NC}"
fi

if ! command_exists npm; then
    echo -e "${RED}❌ npm not found${NC}"
    MISSING_DEPS=1
else
    NPM_VERSION=$(npm --version)
    echo -e "${GREEN}✅ npm found: $NPM_VERSION${NC}"
fi

if ! command_exists docker; then
    echo -e "${YELLOW}⚠️  Docker not found (optional - for Redis)${NC}"
else
    echo -e "${GREEN}✅ Docker found${NC}"
fi

if [ $MISSING_DEPS -eq 1 ]; then
    echo ""
    echo -e "${RED}❌ Missing required dependencies. Please install them first.${NC}"
    exit 1
fi

echo ""
echo "✅ All prerequisites met!"
echo ""

# Check if ports are available
echo "🔍 Checking ports..."
if port_in_use 8000; then
    echo -e "${YELLOW}⚠️  Port 8000 (Backend) is already in use${NC}"
    echo "   Kill the process with: lsof -ti:8000 | xargs kill -9"
    exit 1
fi

if port_in_use 5173; then
    echo -e "${YELLOW}⚠️  Port 5173 (Frontend) is already in use${NC}"
    echo "   Kill the process with: lsof -ti:5173 | xargs kill -9"
    exit 1
fi

if port_in_use 6379; then
    echo -e "${YELLOW}⚠️  Port 6379 (Redis) is already in use - assuming Redis is running${NC}"
    REDIS_RUNNING=1
else
    REDIS_RUNNING=0
fi

echo -e "${GREEN}✅ Ports are available${NC}"
echo ""

# Check Oracle connection details
echo "🔧 Checking configuration..."
if [ -z "$ORACLE_USER" ] || [ -z "$ORACLE_PASSWORD" ] || [ -z "$ORACLE_DSN" ]; then
    echo -e "${RED}❌ Oracle connection not configured${NC}"
    echo ""
    echo "Please set the following environment variables:"
    echo ""
    echo "  export ORACLE_USER=\"your_monitoring_user\""
    echo "  export ORACLE_PASSWORD=\"your_password\""
    echo "  export ORACLE_DSN=\"host:1521/service_name\""
    echo ""
    echo "Or edit backend/.env file with your credentials"
    exit 1
else
    echo -e "${GREEN}✅ Oracle connection configured${NC}"
    echo "   User: $ORACLE_USER"
    echo "   DSN: $ORACLE_DSN"
fi

echo ""

# Start Redis if not running
if [ $REDIS_RUNNING -eq 0 ]; then
    echo "🔴 Starting Redis..."
    if command_exists docker; then
        docker run -d -p 6379:6379 --name query-tuner-redis redis:7-alpine >/dev/null 2>&1
        echo -e "${GREEN}✅ Redis started (Docker)${NC}"
    else
        echo -e "${YELLOW}⚠️  Docker not found. Please start Redis manually:${NC}"
        echo "   redis-server"
        exit 1
    fi
else
    echo -e "${GREEN}✅ Redis already running${NC}"
fi

echo ""

# Set up backend
echo "🔧 Setting up Backend..."
cd backend

if [ ! -d "venv" ]; then
    echo "   Creating virtual environment..."
    python3 -m venv venv
fi

echo "   Activating virtual environment..."
source venv/bin/activate

if [ ! -f "venv/.installed" ]; then
    echo "   Installing dependencies (this may take a few minutes)..."
    pip install -q --upgrade pip
    pip install -q -r requirements/dev.txt
    touch venv/.installed
else
    echo "   Dependencies already installed"
fi

# Export environment variables
export REDIS_URL="redis://localhost:6379"
export ENVIRONMENT="development"
export DEBUG="true"
export LOG_LEVEL="INFO"

echo -e "${GREEN}✅ Backend ready${NC}"
echo ""

# Set up frontend
echo "🔧 Setting up Frontend..."
cd ../frontend

if [ ! -d "node_modules" ]; then
    echo "   Installing dependencies (this may take a few minutes)..."
    npm install --silent
else
    echo "   Dependencies already installed"
fi

echo -e "${GREEN}✅ Frontend ready${NC}"
echo ""

# Start services
echo "🚀 Starting services..."
echo ""

cd ..

# Start backend in background
echo "   Starting Backend API on http://localhost:8000..."
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 > ../logs/backend.log 2>&1 &
BACKEND_PID=$!
echo "   Backend PID: $BACKEND_PID"
cd ..

# Wait a bit for backend to start
sleep 3

# Check if backend started successfully
if ! port_in_use 8000; then
    echo -e "${RED}❌ Backend failed to start. Check logs/backend.log${NC}"
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi

# Start frontend in background
echo "   Starting Frontend on http://localhost:5173..."
cd frontend
npm run dev > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
echo "   Frontend PID: $FRONTEND_PID"
cd ..

# Wait for frontend to start
sleep 5

if ! port_in_use 5173; then
    echo -e "${RED}❌ Frontend failed to start. Check logs/frontend.log${NC}"
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    exit 1
fi

# Create logs directory if it doesn't exist
mkdir -p logs

# Create PID file
echo $BACKEND_PID > logs/backend.pid
echo $FRONTEND_PID > logs/frontend.pid

echo ""
echo "======================================================"
echo -e "${GREEN}✅ All services started successfully!${NC}"
echo "======================================================"
echo ""
echo "🌐 Access the application:"
echo "   Frontend:         http://localhost:5173"
echo "   Backend API:      http://localhost:8000"
echo "   API Docs:         http://localhost:8000/docs"
echo "   Health Check:     http://localhost:8000/health"
echo ""
echo "📊 Monitor logs:"
echo "   Backend:          tail -f logs/backend.log"
echo "   Frontend:         tail -f logs/frontend.log"
echo ""
echo "🛑 To stop all services:"
echo "   ./stop-dev.sh"
echo ""
echo "📖 For detailed testing instructions, see:"
echo "   TESTING_GUIDE.md"
echo ""
echo "Happy testing! 🎉"
