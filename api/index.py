import sys
import os

# Add the root directory to the python path so that 'backend' module can be resolved
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the FastAPI app instance from backend.main
from backend.main import app
