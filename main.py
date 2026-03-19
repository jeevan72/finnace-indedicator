import sys
from pathlib import Path

# Fix python imports to always find src folder explicitly
SRC_DIR = Path(__file__).resolve().parent / "src"
sys.path.append(str(SRC_DIR))

from storage.db import init_db
from cli.app import app

if __name__ == "__main__":
    init_db()  # Ensures database paths exist and schemas sync
    app()
