"""Test Helpers - For fixing import issues."""

import logging
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def fix_imports():
    """Fix imports for tests."""
    import os
    import sys
    from pathlib import Path
    # Add project root to path
    root_dir = Path(__file__).parent.parent
    if str(root_dir) not in sys.path:
        sys.path.insert(0, str(root_dir))
    return root_dir


def safe_import(module_name):
    """Safe import function."""
    try:
        module = __import__(module_name, fromlist=[''])
        return True, module
    except ImportError as e:
        return False, None


def skip_if_not_installed(*modules):
    """Decorator to skip test if module not installed."""
    import pytest
    def decorator(func):
        import functools
        for module in modules:
            try:
                __import__(module)
            except ImportError:
                return pytest.mark.skip(f"Requires {module}")(func)
        return func
    return decorator


# Initialize
PROJECT_ROOT = fix_imports()

