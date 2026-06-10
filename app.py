import sys
import os

# Add backend to sys.path to resolve relative imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

from backend.main import app

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app:app", host="0.0.0.0", port=port)
