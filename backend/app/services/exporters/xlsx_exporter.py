"""XLSX exporter with styled headers and per-data-type tabs."""

from __future__ import annotations

import os
from typing import Any

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter


# Financial theme colors — dark blue headers
HEADER_BG_COLOR = "1B3A5C"
HEADER_FONT_COLOR = "FFFFFF"


PASS_FILL = PatternFill(start_color="E6F4EA", end_color="E6F4EA", fill_type="solid")
FAIL_FILL = PatternFill(start_color="FCE8E6", end_color="FCE8E6", fill_type="solid")
PASS_FONT = Font(color="1B7D3F", size=11)
FAIL_FONT = Font(color="C5221F", bold=True, size=11)


def export_xlsx(
    data_types: dict[str, list[dict[str, Any]]],
    output_dir: str,
    base_name: str = "export",
    validation_checks: list[dict[str, Any]] | None = None,
) -> str:
    """Export data types to a single .xlsx file with one tab per data type.

    Returns the filename of the output file.
    """
    filename = f"{base_name}.xlsx"
    filepath = os.path.join(output_dir, filename)

    wb = Workbook()
    # Remove the default sheet
    wb.remove(wb.active)

    header_font = Font(bold=True, color=HEADER_FONT_COLOR, size=11)
    header_fill = PatternFill(start_color=HEADER_BG_COLOR, end_color=HEADER_BG_COLOR, fill_type="solid")
    header_alignment = Alignment(horizontal="center", vertical="center")

    for dt_name, rows in data_types.items():
        # Sheet name max 31 chars in Excel
        sheet_name = dt_name[:31]
        ws = wb.create_sheet(title=sheet_name)

        if not rows:
            continue

        # Collect all columns across all rows
        columns = _all_columns(rows)

        # Write header row
        for col_idx, col_name in enumerate(columns, 1):
            cell = ws.cell(row=1, column=col_idx, value=str(col_name))
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = header_alignment

        # Write data rows with explicit types
        for row_idx, row in enumerate(rows, 2):
            for col_idx, col_name in enumerate(columns, 1):
                value = row.get(col_name, "")
                if value is None:
                    value = ""
                # Try to convert numeric strings to numbers for proper Excel formatting
                cell_value = _typed_value(value)
                cell = ws.cell(row=row_idx, column=col_idx, value=cell_value)

        # Auto-width columns based on content
        for col_idx, col_name in enumerate(columns, 1):
            max_width = len(str(col_name))
            # Sample first 100 rows to determine width
            for row_idx in range(2, min(len(rows) + 2, 102)):
                cell_val = ws.cell(row=row_idx, column=col_idx).value
                if cell_val is not None:
                    max_width = max(max_width, len(str(cell_val)))
            # Cap at 50 chars, add padding
            adjusted_width = min(max_width + 3, 50)
            ws.column_dimensions[get_column_letter(col_idx)].width = adjusted_width

    # Add Validation sheet if checks are provided
    if validation_checks:
        vs = wb.create_sheet(title="Validation", index=0)
        val_headers = ["Section", "Check", "Declared (XAF)", "Computed", "Result"]
        val_header_font = Font(bold=True, color=HEADER_FONT_COLOR, size=11)
        val_header_fill = PatternFill(start_color=HEADER_BG_COLOR, end_color=HEADER_BG_COLOR, fill_type="solid")

        for col_idx, h in enumerate(val_headers, 1):
            cell = vs.cell(row=1, column=col_idx, value=h)
            cell.font = val_header_font
            cell.fill = val_header_fill
            cell.alignment = header_alignment

        for row_idx, vc in enumerate(validation_checks, 2):
            passed = vc.get("passed", False)
            row_fill = PASS_FILL if passed else FAIL_FILL
            row_font = PASS_FONT if passed else FAIL_FONT
            result_text = "PASS" if passed else "FAIL"

            values = [
                vc.get("section", ""),
                vc.get("check", ""),
                vc.get("declared", ""),
                vc.get("computed", ""),
                result_text,
            ]
            for col_idx, val in enumerate(values, 1):
                cell = vs.cell(row=row_idx, column=col_idx, value=val)
                cell.fill = row_fill
                if col_idx == 5:
                    cell.font = row_font

        for col_idx in range(1, 6):
            vs.column_dimensions[get_column_letter(col_idx)].width = 22

    # Ensure at least one sheet exists
    if len(wb.sheetnames) == 0:
        wb.create_sheet(title="Empty")

    wb.save(filepath)
    return filename


def _all_columns(rows: list[dict[str, Any]]) -> list[str]:
    """Collect all unique column names across all rows, preserving order."""
    seen: dict[str, None] = {}
    for row in rows:
        for key in row:
            if key not in seen:
                seen[key] = None
    return list(seen.keys())


def _typed_value(value: Any) -> Any:
    """Convert value to appropriate Excel type.

    Strings are kept as strings (explicit type).
    Numeric strings that look like amounts are converted to float.
    """
    if not isinstance(value, str):
        return value
    if value == "":
        return ""
    # Try float conversion for numeric-looking values
    try:
        fval = float(value)
        # Preserve integer appearance
        if fval == int(fval) and "." not in value:
            return int(fval)
        return fval
    except (ValueError, OverflowError):
        return str(value)
