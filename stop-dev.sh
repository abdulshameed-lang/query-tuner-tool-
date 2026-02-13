#!/bin/bash

# Stop script for Oracle Query Tuner Tool development services

echo "🛑 Stopping Oracle Query Tuner Tool services..."
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Stop services by PID if PID files exist
if [ -f "logs/backend.pid" ]; then
    BACKEND_PID=$(cat logs/backend.pid)
    if ps -p $BACKEND_PID > /dev/null 2>&1; then
        echo "   Stopping Backend (PID: $BACKEND_PID)..."
        kill $BACKEND_PID 2>/dev/null
        echo -e "${GREEN}✅ Backend stopped${NC}"
    else
        echo -e "${YELLOW}⚠️  Backend process not found${NC}"
    fi
    rm logs/backend.pid
fi

if [ -f "logs/frontend.pid" ]; then
    FRONTEND_PID=$(cat logs/frontend.pid)
    if ps -p $FRONTEND_PID > /dev/null 2>&1; then
        echo "   Stopping Frontend (PID: $FRONTEND_PID)..."
        kill $FRONTEND_PID 2>/dev/null
        echo -e "${GREEN}✅ Frontend stopped${NC}"
    else
        echo -e "${YELLOW}⚠️  Frontend process not found${NC}"
    fi
    rm logs/frontend.pid
fi

# Fallback: Kill any processes on the ports
echo ""
echo "   Checking for any remaining processes on ports..."

if lsof -ti:8000 >/dev/null 2>&1; then
    echo "   Killing process on port 8000 (Backend)..."
    lsof -ti:8000 | xargs kill -9 2>/dev/null
fi

if lsof -ti:5173 >/dev/null 2>&1; then
    echo "   Killing process on port 5173 (Frontend)..."
    lsof -ti:5173 | xargs kill -9 2>/dev/null
fi

# Ask about Redis
echo ""
read -p "Stop Redis container? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if docker ps | grep -q "query-tuner-redis"; then
        echo "   Stopping Redis container..."
        docker stop query-tuner-redis >/dev/null 2>&1
        docker rm query-tuner-redis >/dev/null 2>&1
        echo -e "${GREEN}✅ Redis stopped${NC}"
    else
        echo -e "${YELLOW}⚠️  Redis container not found${NC}"
    fi
fi

echo ""
echo -e "${GREEN}✅ All services stopped${NC}"
