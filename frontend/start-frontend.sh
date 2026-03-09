#!/bin/bash
# SwiftReply Frontend Start Script
set -e

echo "🎨 Starting SwiftReply Frontend..."

if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
fi

echo "✅ Starting Vite dev server on port 5173..."
npm run dev
