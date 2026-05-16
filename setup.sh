#!/bin/bash
# Neural Agent System - Setup Script
# 一键配置安装环境

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

echo "============================================="
echo "  Neural Agent System - Installation Setup"
echo "============================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print success message
print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

# Print info message
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

# Print warning message
print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Print error message
print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Step 1: Check Python version
print_info "Step 1: Checking Python version..."
PYTHON_CMD=""
if command -v python3.10 &> /dev/null; then
    PYTHON_CMD=python3.10
elif command -v python3.11 &> /dev/null; then
    PYTHON_CMD=python3.11
elif command -v python3.12 &> /dev/null; then
    PYTHON_CMD=python3.12
elif command -v python3.13 &> /dev/null; then
    PYTHON_CMD=python3.13
elif command -v python3.14 &> /dev/null; then
    PYTHON_CMD=python3.14
elif command -v python3 &> /dev/null; then
    PYTHON_CMD=python3
elif command -v python &> /dev/null; then
    PYTHON_CMD=python
else
    print_error "Python not found! Please install Python 3.10 or higher."
    exit 1
fi

PYTHON_VERSION=$($PYTHON_CMD --version | cut -d' ' -f2)
print_success "Found Python $PYTHON_VERSION at $(which $PYTHON_CMD)"

# Step 2: Create virtual environment
print_info ""
print_info "Step 2: Creating virtual environment..."
VENV_DIR=".venv"

if [ -d "$VENV_DIR" ]; then
    print_warning "Virtual environment already exists. Removing..."
    rm -rf "$VENV_DIR"
fi

$PYTHON_CMD -m venv "$VENV_DIR"
print_success "Virtual environment created at $VENV_DIR"

# Activate virtual environment
source "$VENV_DIR/bin/activate"
print_success "Virtual environment activated"

# Step 3: Upgrade pip
print_info ""
print_info "Step 3: Upgrading pip..."
pip install --upgrade pip setuptools wheel
print_success "Pip upgraded"

# Step 4: Install dependencies
print_info ""
print_info "Step 4: Installing dependencies..."
echo ""
echo "Select installation type:"
echo "1) Minimal (Recommended for testing and development)"
echo "2) Full (All features including databases, vector stores, etc.)"
echo ""
read -p "Enter your choice (1/2, default: 1): " INSTALL_CHOICE
INSTALL_CHOICE=${INSTALL_CHOICE:-1}

if [ "$INSTALL_CHOICE" = "2" ]; then
    print_info "Installing full dependencies..."
    pip install -r requirements.txt
else
    print_info "Installing minimal dependencies..."
    pip install -r requirements-minimal.txt
fi

print_success "Dependencies installed"

# Step 5: Setup environment variables
print_info ""
print_info "Step 5: Setting up environment variables..."
if [ ! -f ".env" ]; then
    cp .env.example .env
    print_success ".env file created from .env.example"
    print_warning "Please edit .env file to set your actual API keys and configuration!"
else
    print_warning ".env file already exists, skipping creation"
fi

# Step 6: Run basic verification
print_info ""
print_info "Step 6: Verifying installation..."
python -c "
import sys
print('Python version:', sys.version)
print('Python executable:', sys.executable)

try:
    import fastapi
    print('✓ fastapi installed:', fastapi.__version__)
except ImportError:
    print('✗ fastapi not installed')

try:
    import pydantic
    print('✓ pydantic installed:', pydantic.__version__)
except ImportError:
    print('✗ pydantic not installed')

try:
    import tenacity
    print('✓ tenacity installed:', tenacity.__version__)
except ImportError:
    print('✗ tenacity not installed')

try:
    import pybreaker
    print('✓ pybreaker installed')
except ImportError:
    print('✗ pybreaker not installed')

try:
    import prometheus_client
    print('✓ prometheus_client installed:', prometheus_client.__version__)
except ImportError:
    print('✗ prometheus_client not installed')

try:
    import litellm
    print('✓ litellm installed:', litellm.__version__)
except ImportError:
    print('✗ litellm not installed')

try:
    import structlog
    print('✓ structlog installed')
except ImportError:
    print('✗ structlog not installed')

try:
    import psutil
    print('✓ psutil installed:', psutil.__version__)
except ImportError:
    print('✗ psutil not installed')

print()
print('Installation verification complete!')
"

print_info ""
print_info "============================================="
print_success "Setup complete!"
print_info "============================================="
print_info ""
print_info "To activate the virtual environment, run:"
print_info "  source $VENV_DIR/bin/activate"
print_info ""
print_info "To run the tests, use:"
print_info "  pytest tests/ -v"
print_info ""
print_info "To run the API server, use:"
print_info "  uvicorn backend.main:app --reload"
print_info ""
print_info "Don't forget to edit .env file with your actual configuration!"
print_info ""
