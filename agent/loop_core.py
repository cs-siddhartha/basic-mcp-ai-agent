from __future__ import annotations

def extract_first_line(response_text: str | None) -> str:
    return (response_text or "").strip().splitlines()[0].strip()


def parse_function_call(line: str) -> tuple[str, list[str]]:
    _, call = line.split(":", 1)
    parts = [part.strip() for part in call.split("|")]
    return parts[0], parts[1:]
