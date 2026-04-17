"""JSON exporter with ensure_ascii=True for security."""

from __future__ import annotations

import json
import os
from typing import Any


def export_json(
    data_types: dict[str, list[dict[str, Any]]],
    output_dir: str,
    base_name: str = "export",
) -> str:
    """Export data types to a structured JSON file.

    Output format: {"data_type_name": [records], ...}

    Returns the filename of the output file.
    """
    filename = f"{base_name}.json"
    filepath = os.path.join(output_dir, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data_types, f, ensure_ascii=True, indent=2)

    return filename
