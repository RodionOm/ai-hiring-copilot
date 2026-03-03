# utils.py
import json
from typing import Any, Dict

def read_text_file(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def safe_json_loads(text: str) -> Dict[str, Any]:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"error": "Invalid JSON returned by the model", "raw": text}