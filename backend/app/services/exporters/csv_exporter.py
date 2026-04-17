"""CSV exporter with formula injection prevention."""

from __future__ import annotations

import csv
import io
import os
import zipfile
from typing import Any


def export_csv(
    data_types: dict[str, list[dict[str, Any]]],
    output_dir: str,
    base_name: str = "export",
) -> str:
    """Export data types to CSV file(s).

    If multiple data types, creates a .zip containing separate .csv files.
    If single data type, creates a single .csv file.

    Returns the filename of the output file.
    """
    if len(data_types) == 1:
        name = list(data_types.keys())[0]
        rows = list(data_types.values())[0]
        filename = f"{base_name}-{name}.csv"
        filepath = os.path.join(output_dir, filename)
        _write_csv(filepath, rows)
        return filename
    else:
        zip_filename = f"{base_name}.zip"
        zip_path = os.path.join(output_dir, zip_filename)
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for name, rows in data_types.items():
                csv_content = _csv_to_string(rows)
                zf.writestr(f"{name}.csv", csv_content)
        return zip_filename


def _all_fieldnames(rows: list[dict[str, Any]]) -> list[str]:
    """Collect all unique field names across all rows, preserving order."""
    seen: dict[str, None] = {}
    for row in rows:
        for key in row:
            if key not in seen:
                seen[key] = None
    return list(seen.keys())


def _write_csv(filepath: str, rows: list[dict[str, Any]]) -> None:
    """Write rows to a CSV file with QUOTE_ALL for formula injection prevention."""
    if not rows:
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            f.write("")
        return

    fieldnames = _all_fieldnames(rows)
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=fieldnames, quoting=csv.QUOTE_ALL,
            extrasaction="ignore", restval="",
        )
        writer.writeheader()
        writer.writerows(rows)


def _csv_to_string(rows: list[dict[str, Any]]) -> str:
    """Write rows to a CSV string with QUOTE_ALL."""
    if not rows:
        return ""

    fieldnames = _all_fieldnames(rows)
    output = io.StringIO()
    writer = csv.DictWriter(
        output, fieldnames=fieldnames, quoting=csv.QUOTE_ALL,
        extrasaction="ignore", restval="",
    )
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue()
