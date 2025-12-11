"""
Utility JSON helpers
"""

import json
import os


def save_json(data: dict, path: str):
    """
    Save a Python object to a JSON file with UTF-8 encoding.
    """
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
