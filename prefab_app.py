"""
Render the latest MCP FINAL_ANSWER Prefab JSON from data/ui_payload.json.

Run:
  prefab serve prefab_app.py
"""

from __future__ import annotations

import json
from pathlib import Path

from prefab_ui.app import PrefabApp
from prefab_ui.actions.mcp import CallTool
from prefab_ui.components import (
  Badge,
  Button,
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Column,
  Form,
  H3,
  Input,
  Muted,
  Row,
  Tab,
  Tabs,
  Text,
)


PAYLOAD_FILE = Path("data/ui_payload.json")


def load_payload() -> dict:
  """Load saved Prefab payload or return an empty fallback."""
  if not PAYLOAD_FILE.exists():
    return {
      "type": "prefab",
      "view": "search_results_with_actions",
      "payload": {
        "search_summary": "No payload yet. Run main.py first.",
        "search_results": [],
        "suggested_actions": [
          "create_record(title, content)",
          "list_records()",
          "update_record(record_id, content)",
          "delete_record(record_id)",
        ],
        "next_step_hint": "Select a result and trigger CRUD manually from your UI/client action flow.",
      },
    }
  try:
    return json.loads(PAYLOAD_FILE.read_text(encoding="utf-8"))
  except json.JSONDecodeError:
    return {
      "type": "prefab",
      "view": "search_results_with_actions",
      "payload": {
        "search_summary": "Invalid JSON in data/ui_payload.json",
        "search_results": [],
        "suggested_actions": [],
        "next_step_hint": "",
      },
    }


ui = load_payload()
payload = ui.get("payload", {})
results = payload.get("search_results", [])
actions = payload.get("suggested_actions", [])

with PrefabApp(css_class="max-w-3xl mx-auto p-6") as app:
  with Card():
    with CardHeader():
      CardTitle("MCP Search + User CRUD Actions")
      Badge(f"View: {ui.get('view', 'unknown')}", variant="default")
    with CardContent():
      with Tabs(value="results"):
        with Tab("Search Results", value="results"):
          with Column(gap=3):
            H3("Search Summary")
            Text(str(payload.get("search_summary", "")))
            if not results:
              Muted("No results in payload.")
            for idx, result in enumerate(results, start=1):
              with Card():
                with CardContent():
                  with Column(gap=1):
                    Text(f"{idx}. {result.get('title', 'Untitled')}")
                    Muted(result.get("url", ""))
                    Muted(result.get("snippet", ""))
        with Tab("CRUD Actions (User)", value="actions"):
          with Column(gap=3):
            H3("Suggested CRUD Actions")
            if not actions:
              Muted("No actions were provided by the agent.")
            for action in actions:
              with Row(gap=2):
                Badge("Action", variant="default")
                Text(str(action))
            H3("Next Step")
            Muted(str(payload.get("next_step_hint", "")))
            H3("Create Record")
            with Form(on_submit=CallTool("create_record")):
              Input(name="title", placeholder="Record title")
              Input(name="content", placeholder="Record content")
              Button("Create Record")
            H3("List Records")
            Button("Refresh Record List", variant="outline", on_click=CallTool("list_records"))
            H3("Update Record")
            with Form(on_submit=CallTool("update_record")):
              Input(name="record_id", placeholder="Record ID")
              Input(name="content", placeholder="Updated content")
              Button("Update Record")
            H3("Delete Record")
            with Form(on_submit=CallTool("delete_record")):
              Input(name="record_id", placeholder="Record ID")
              Button("Delete Record", variant="destructive")
