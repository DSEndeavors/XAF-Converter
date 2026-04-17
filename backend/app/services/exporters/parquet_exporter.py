"""Parquet exporter with explicit pyarrow schema (no inference)."""

from __future__ import annotations

import os
import zipfile
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq


def export_parquet(
    data_types: dict[str, list[dict[str, Any]]],
    output_dir: str,
    base_name: str = "export",
) -> str:
    """Export data types to Parquet file(s).

    If multiple data types, creates separate .parquet files in a .zip.
    If single data type, creates a single .parquet file.

    Returns the filename of the output file.
    """
    if len(data_types) == 1:
        name = list(data_types.keys())[0]
        rows = list(data_types.values())[0]
        filename = f"{base_name}-{name}.parquet"
        filepath = os.path.join(output_dir, filename)
        _write_parquet(filepath, rows)
        return filename
    else:
        zip_filename = f"{base_name}.zip"
        zip_path = os.path.join(output_dir, zip_filename)
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for name, rows in data_types.items():
                parquet_path = os.path.join(output_dir, f"{name}.parquet")
                _write_parquet(parquet_path, rows)
                zf.write(parquet_path, f"{name}.parquet")
                # Remove the individual file after adding to zip
                os.remove(parquet_path)
        return zip_filename


def _write_parquet(filepath: str, rows: list[dict[str, Any]]) -> None:
    """Write rows to a Parquet file with an explicit schema."""
    if not rows:
        # Write empty parquet with no columns
        schema = pa.schema([])
        table = pa.table({}, schema=schema)
        pq.write_table(table, filepath)
        return

    # Build explicit schema from all rows (columns may vary)
    columns = _all_columns(rows)
    fields = []
    for col in columns:
        # Determine type from data: check if all non-None values are numeric
        is_numeric = _is_numeric_column(col, rows)
        if is_numeric:
            fields.append(pa.field(col, pa.float64()))
        else:
            fields.append(pa.field(col, pa.string()))

    schema = pa.schema(fields)

    # Build column arrays
    arrays = {}
    for col_idx, col in enumerate(columns):
        is_numeric = schema.field(col_idx).type == pa.float64()
        if is_numeric:
            values = []
            for row in rows:
                val = row.get(col)
                if val is None or val == "":
                    values.append(None)
                else:
                    try:
                        values.append(float(val))
                    except (ValueError, TypeError):
                        values.append(None)
            arrays[col] = pa.array(values, type=pa.float64())
        else:
            values = [str(row.get(col, "")) if row.get(col) is not None else None for row in rows]
            arrays[col] = pa.array(values, type=pa.string())

    table = pa.table(arrays, schema=schema)
    pq.write_table(table, filepath)


def _all_columns(rows: list[dict[str, Any]]) -> list[str]:
    """Collect all unique column names across all rows, preserving order."""
    seen: dict[str, None] = {}
    for row in rows:
        for key in row:
            if key not in seen:
                seen[key] = None
    return list(seen.keys())


def _is_numeric_column(col_name: str, rows: list[dict[str, Any]]) -> bool:
    """Check if a column contains numeric data by sampling."""
    # Known numeric column names (amounts, counts, percentages)
    numeric_indicators = {"amnt", "totalDebit", "totalCredit", "linesCount",
                          "vatPerc", "vatAmnt", "curAmnt", "opBalDesc", "clBalDesc",
                          "custCreditLimit", "supplierLimit", "qntty"}
    if col_name in numeric_indicators:
        return True

    # Sample first 20 rows
    sample = rows[:20]
    numeric_count = 0
    non_empty_count = 0
    for row in sample:
        val = row.get(col_name)
        if val is not None and val != "":
            non_empty_count += 1
            try:
                float(str(val))
                numeric_count += 1
            except (ValueError, TypeError):
                pass

    # If all non-empty values are numeric and there is at least one, treat as numeric
    return non_empty_count > 0 and numeric_count == non_empty_count
