import json
from pathlib import Path
from uuid import uuid4

DATA_DIR = Path("data")
DATA_FILE = DATA_DIR / "items.json"


def _ensure_store() -> None:
  """Create the data directory and JSON file if missing."""
  DATA_DIR.mkdir(parents=True, exist_ok=True)
  if not DATA_FILE.exists():
    DATA_FILE.write_text("[]", encoding="utf-8")


def _read_all() -> list[dict]:
  """Read all records from disk; return an empty list on decode failure."""
  _ensure_store()
  try:
    return json.loads(DATA_FILE.read_text(encoding="utf-8"))
  except json.JSONDecodeError:
    return []


def _write_all(items: list[dict]) -> None:
  """Persist the full record list to disk."""
  _ensure_store()
  DATA_FILE.write_text(json.dumps(items, indent=2), encoding="utf-8")


def create_record(title: str, content: str) -> dict:
  """Create and store a new record with a generated UUID."""
  items = _read_all()
  record = {
    "id": str(uuid4()),
    "title": title,
    "content": content,
  }
  items.append(record)
  _write_all(items)
  return record


def list_records() -> list[dict]:
  """Return all stored records."""
  return _read_all()


def update_record(record_id: str, content: str) -> dict | None:
  """Update one record by ID and return it, or None if not found."""
  items = _read_all()
  for item in items:
    if item.get("id") == record_id:
      item["content"] = content
      _write_all(items)
      return item
  return None


def delete_record(record_id: str) -> bool:
  """Delete one record by ID; return True when deleted."""
  items = _read_all()
  next_items = [item for item in items if item.get("id") != record_id]
  if len(next_items) == len(items):
    return False
  _write_all(next_items)
  return True
