#!/bin/bash

# PatchPilot Frontend Startup Script
# This script sets up and runs the Jekyll frontend

echo "🚀 Starting PatchPilot Frontend..."

# Check if we're in the right directory
if [ ! -f "frontend/_config.yml" ]; then
    echo "❌ Error: Please run this script from the project root directory"
    echo "   Expected: frontend/_config.yml"
    exit 1
fi

# Navigate to frontend directory
cd frontend

# Check if Ruby is installed
if ! command -v ruby &> /dev/null; then
    echo "❌ Error: Ruby is not installed"
    echo "   Please install Ruby 2.7 or higher"
    exit 1
fi

# Check if Bundler is installed
if ! command -v bundle &> /dev/null; then
    echo "📦 Installing Bundler..."
    gem install bundler
fi

# Install dependencies
echo "📦 Installing Ruby dependencies..."
bundle install

# Check if the API server is running
echo "🔍 Checking API server status..."
if curl -s http://localhost:8000/docs > /dev/null 2>&1; then
    echo "✅ API server is running on http://localhost:8000"
else
    echo "⚠️  Warning: API server doesn't seem to be running on http://localhost:8000"
    echo "   Make sure to start the FastAPI server first:"
    echo "   python run.py"
    echo ""
    echo "   Or update the api_base_url in frontend/_config.yml"
fi

# Start Jekyll server
echo "🌐 Starting Jekyll server..."
echo "   Frontend will be available at: http://localhost:4000"
echo "   Press Ctrl+C to stop the server"
echo ""

bundle exec jekyll serve --livereload --host 0.0.0.0 