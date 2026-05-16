#!/bin/bash
# NeuralAgent Architecture Visualization - Quick Start

echo "=============================================="
echo "  NeuralAgent Architecture Visualization"
echo "=============================================="
echo ""

cd "$(dirname "$0")/arch-visualization"

echo "Checking dependencies..."
npm install --silent

echo ""
echo "Starting development server..."
echo "=============================================="
echo "  Visualization will open at:"
echo "  http://localhost:5173"
echo "=============================================="
echo ""

npm run dev
