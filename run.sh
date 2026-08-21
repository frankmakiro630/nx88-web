#!/bin/bash

# NX88 Casino - Backend Startup Script

set -e  # Exit on error

echo "🎰 NX88 Casino Backend - Startup"
echo "=================================="

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found!"
    echo "Creating .env from .env.example..."
    cp .env.example .env
    echo "✏️  Please edit .env with your Discord OAuth credentials"
    exit 1
fi

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.8 or higher."
    exit 1
fi

echo "✅ Python $(python3 --version) found"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📚 Installing dependencies..."
pip install -q -r requirements.txt

# Check if Docker containers are running
if command -v docker &> /dev/null; then
    echo "🐳 Checking Docker containers..."
    
    if ! docker ps | grep -q nx88_postgres; then
        echo "⚠️  PostgreSQL container not running"
        echo "Starting Docker containers..."
        docker-compose up -d
        echo "⏳ Waiting for database to be ready..."
        sleep 5
    fi
fi

# Start the server
echo ""
echo "🚀 Starting NX88 Casino API Server..."
echo "📍 Server: http://localhost:8000"
echo "📚 Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop"
echo ""

python main.py
