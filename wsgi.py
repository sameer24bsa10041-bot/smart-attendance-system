import sys
import os

# Add your app directory to the Python path
path = '/home/yourusername/smart-attendance-system'
if path not in sys.path:
    sys.path.append(path)

from app import app as application