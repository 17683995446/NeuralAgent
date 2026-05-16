#!/bin/bash
# Neural Agent System - Quick Setup Script
# 快速配置安装环境 (非交互式)

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

echo "============================================="
echo "  Neural Agent System - Quick Setup"
echo "============================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

# Step 1: Find Python
print_info "Step 1: Finding Python..."
PYTHON_CMD=""
for py_cmd in python3.14 python3.13 python3.12 python3.11 python3.10 python3 python; do
    if command -v $py_cmd &> /dev/null; then
        PYTHON_CMD=$py_cmd
        break
    fi
done

if [ -z "$PYTHON_CMD" ]; then
    echo "Error: Python not found!"
    exit 1
fi

PYTHON_VERSION=$($PYTHON_CMD --version)
print_success "Using $PYTHON_VERSION"

# Step 2: Create virtual environment
print_info ""
print_info "Step 2: Creating virtual environment..."
VENV_DIR=".venv"

if [ -d "$VENV_DIR" ]; then
    echo "Virtual environment exists, removing..."
    rm -rf "$VENV_DIR"
fi

$PYTHON_CMD -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"
print_success "Virtual environment created and activated"

# Step 3: Upgrade pip
print_info ""
print_info "Step 3: Upgrading pip..."
pip install --upgrade pip setuptools wheel -q
print_success "Pip upgraded"

# Step 4: Install minimal dependencies
print_info ""
print_info "Step 4: Installing minimal dependencies (this may take a few minutes)..."
pip install -r requirements-minimal.txt -q
print_success "Dependencies installed"

# Step 5: Setup environment variables
print_info ""
print_info "Step 5: Setting up environment..."
if [ ! -f ".env" ]; then
    cp .env.example .env
    print_success ".env file created"
fi

# Step 6: Verify installation
print_info ""
print_info "Step 6: Verifying installation..."
python -c "
import sys
print('✓ Python version:', sys.version.split()[0])

modules = [
    ('fastapi', 'fastapi'),
    ('pydantic', 'pydantic'),
    ('tenacity', 'tenacity'),
    ('pybreaker', 'pybreaker'),
    ('prometheus_client', 'prometheus-client'),
    ('litellm', 'litellm'),
    ('structlog', 'structlog'),
    ('psutil', 'psutil'),
]

all_good = True
for mod_name, pkg_name in modules:
    try:
        mod = __import__(mod_name)
        version = getattr(mod, '__version__', 'OK')
        print(f'✓ {pkg_name}: {version}')
    except ImportError:
        print(f'✗ {pkg_name}: NOT INSTALLED')
        all_good = False

print()
if all_good:
    print('All core modules installed successfully!')
else:
    print('Some modules are missing, but basic functionality should work.')
"

print_info ""
print_info "============================================="
print_success "Quick setup complete!"
print_info "============================================="
print_info ""
print_info "Next steps:"
print_info "  1. Activate virtual environment:"
print_info "     source .venv/bin/activate"
print_info ""
print_info "  2. Run tests:"
print_info "     pytest tests/test_performance_optimizer.py -v"
print_info ""
print_info "  3. (Optional) Edit .env for full feature configuration"
print_info ""
