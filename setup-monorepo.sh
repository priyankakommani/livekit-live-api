#!/bin/bash

echo "╔═══════════════════════════════════════════════════════════╗"
echo "║                                                           ║"
echo "║   🚀 AI Interview System - Setup Script                  ║"
echo "║                                                           ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 20.9+ first."
    exit 1
fi

echo "✅ Node.js version: $(node --version)"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python is not installed. Please install Python 3.10+ first."
    exit 1
fi

echo "✅ Python version: $(python3 --version)"
echo ""

# Install backend dependencies
echo "📦 Installing backend dependencies..."
cd backend
npm install --no-audit
if [ $? -eq 0 ]; then
    echo "✅ Backend dependencies installed"
else
    echo "❌ Failed to install backend dependencies"
    exit 1
fi
cd ..
echo ""

# Install frontend dependencies
echo "📦 Installing frontend dependencies..."
cd frontend
npm install --no-audit
if [ $? -eq 0 ]; then
    echo "✅ Frontend dependencies installed"
else
    echo "❌ Failed to install frontend dependencies"
    exit 1
fi
cd ..
echo ""

# Check Python dependencies
echo "📦 Checking Python dependencies..."
cd src
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate
pip install -r ../requirements.txt --quiet
if [ $? -eq 0 ]; then
    echo "✅ Python dependencies installed"
else
    echo "❌ Failed to install Python dependencies"
    exit 1
fi
deactivate
cd ..
echo ""

echo "╔═══════════════════════════════════════════════════════════╗"
echo "║                                                           ║"
echo "║   ✅ Setup Complete!                                      ║"
echo "║                                                           ║"
echo "║   Next steps:                                             ║"
echo "║   1. Open 3 terminal windows                              ║"
echo "║   2. Terminal 1: cd backend && npm start                  ║"
echo "║   3. Terminal 2: cd frontend && npm run dev               ║"
echo "║   4. Terminal 3: cd src && python agent.py dev            ║"
echo "║                                                           ║"
echo "║   Then open: http://localhost:5173                        ║"
echo "║                                                           ║"
echo "╚═══════════════════════════════════════════════════════════╝"
