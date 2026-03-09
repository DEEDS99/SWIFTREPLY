#!/bin/bash
# SwiftReply Backend Start Script
set -e

echo "🚀 Starting SwiftReply Backend..."

# Load env
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Install dependencies if needed
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python -m venv venv
fi

source venv/bin/activate
pip install -r requirements.txt -q

# Run migrations
echo "🗄️  Running database migrations..."
alembic upgrade head 2>/dev/null || echo "⚠️  Alembic migration skipped (run manually if needed)"

# Start server
echo "✅ Starting Uvicorn on port ${BACKEND_PORT:-8000}..."
uvicorn app.main:app \
    --host 0.0.0.0 \
    --port ${BACKEND_PORT:-8000} \
    --reload \
    --log-level info
