"""
JobSwipe Backend Package
"""

import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

__version__ = "1.0.0"

# Avoid eager submodule imports to prevent side effects during test discovery
__all__ = ["__version__"]
