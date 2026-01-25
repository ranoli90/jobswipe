"""
JobSwipe Backend Package
"""

import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

__version__ = "1.0.0"

# Export submodules
from . import db
from . import api
from . import services
from . import workers

