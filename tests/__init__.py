"""Test package initialization"""
import sys
from pathlib import Path

# Add app to path for testing
app_dir = Path(__file__).parent.parent
sys.path.insert(0, str(app_dir))

