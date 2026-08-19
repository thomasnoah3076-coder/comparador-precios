from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "database" / "tracker.db"

print(DB_PATH)