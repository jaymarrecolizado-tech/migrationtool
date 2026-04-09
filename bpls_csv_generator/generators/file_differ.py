"""
File Differ — Compare two migration files side-by-side.
"""

import csv
import os
from dataclasses import dataclass
from typing import Any


@dataclass
class DiffRecord:
    sheet: str
    key: str
    field: str
    file_a_value: Any
    file_b_value: Any
    change_type: str  # "added", "removed", "modified"


@dataclass
class DiffReport:
    records: list[DiffRecord]
    summary: dict

    def to_dict(self) -> dict:
        return {
            "summary": self.summary,
            "changes": [
                {
                    "sheet": r.sheet,
                    "key": r.key,
                    "field": r.field,
                    "file_a": str(r.file_a_value),
                    "file_b": str(r.file_b_value),
                    "change_type": r.change_type,
                }
                for r in self.records
            ],
        }


class FileDiffer:
    """Compare two Excel/CSV migration files and report differences."""

    def __init__(self, key_field: str = "bin"):
        self.key_field = key_field

    def compare_files(self, file_a: str, file_b: str) -> DiffReport:
        """Compare two files and produce a diff report."""
        import pandas as pd

        sheets_a = self._read_file(file_a)
        sheets_b = self._read_file(file_b)

        records = []
        sheet_stats = {}

        common_sheets = set(sheets_a.keys()) & set(sheets_b.keys())

        for sheet_name in common_sheets:
            rows_a = {self._row_key(row): row for row in sheets_a[sheet_name]}
            rows_b = {self._row_key(row): row for row in sheets_b[sheet_name]}

            all_keys = set(rows_a.keys()) | set(rows_b.keys())
            all_fields = set()
            for row in list(rows_a.values()) + list(rows_b.values()):
                all_fields.update(row.keys())

            sheet_changes = {"added": 0, "removed": 0, "modified": 0}

            for key in all_keys:
                row_a = rows_a.get(key)
                row_b = rows_b.get(key)

                if row_a is None:
                    sheet_changes["added"] += 1
                    for field in all_fields:
                        if field != self.key_field and row_b.get(field) is not None:
                            records.append(
                                DiffRecord(
                                    sheet=sheet_name,
                                    key=str(key),
                                    field=field,
                                    file_a_value=None,
                                    file_b_value=row_b.get(field),
                                    change_type="added",
                                )
                            )
                elif row_b is None:
                    sheet_changes["removed"] += 1
                    for field in all_fields:
                        if field != self.key_field and row_a.get(field) is not None:
                            records.append(
                                DiffRecord(
                                    sheet=sheet_name,
                                    key=str(key),
                                    field=field,
                                    file_a_value=row_a.get(field),
                                    file_b_value=None,
                                    change_type="removed",
                                )
                            )
                else:
                    for field in all_fields:
                        val_a = row_a.get(field)
                        val_b = row_b.get(field)
                        if self._values_differ(val_a, val_b):
                            sheet_changes["modified"] += 1
                            records.append(
                                DiffRecord(
                                    sheet=sheet_name,
                                    key=str(key),
                                    field=field,
                                    file_a_value=val_a,
                                    file_b_value=val_b,
                                    change_type="modified",
                                )
                            )

            if any(v > 0 for v in sheet_changes.values()):
                sheet_stats[sheet_name] = sheet_changes

        total_changes = len(records)
        return DiffReport(
            records=records,
            summary={
                "total_changes": total_changes,
                "sheets_compared": list(common_sheets),
                "sheet_stats": sheet_stats,
            },
        )

    def generate_csv_report(self, report: DiffReport, output_path: str) -> str:
        """Write diff report to CSV."""
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        with open(output_path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(["sheet", "key", "field", "file_a_value", "file_b_value", "change_type"])
            for r in report.records:
                writer.writerow([r.sheet, r.key, r.field, r.file_a_value, r.file_b_value, r.change_type])
        return output_path

    def _read_file(self, filepath: str) -> dict[str, list[dict]]:
        import pandas as pd

        result = {}
        if filepath.endswith((".xls", ".xlsx")):
            xl = pd.ExcelFile(filepath)
            for sheet_name in xl.sheet_names:
                df = pd.read_excel(xl, sheet_name=sheet_name)
                result[sheet_name] = df.where(pd.notnull(df), None).to_dict("records")
        else:
            df = pd.read_csv(filepath)
            result["Sheet1"] = df.where(pd.notnull(df), None).to_dict("records")
        return result

    def _row_key(self, row: dict) -> str:
        """Get unique key for a row."""
        # Try key_field first, then fall back to all values as composite key
        if self.key_field in row and row[self.key_field] is not None:
            return str(row[self.key_field]).strip().lower()
        # Composite key from all non-None values
        parts = [f"{k}={v}" for k, v in sorted(row.items()) if v is not None]
        return "|".join(parts)

    def _values_differ(self, a, b) -> bool:
        if a is None and b is None:
            return False
        if a is None or b is None:
            return True
        return str(a).strip().lower() != str(b).strip().lower()
