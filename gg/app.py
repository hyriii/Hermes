"""
Hermes / أبو محسوب لعدم الرسوب

Entry point – delegates to the interface module.
"""

import sys
import os

# Ensure project root is on the path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from interface import main

if __name__ == "__main__":
    main()