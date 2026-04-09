"""
Duplicate Detector — Find duplicate BINs, OR numbers, business names, and other key fields.
"""

from collections import Counter
from dataclasses import dataclass
from typing import Any


@dataclass
class DuplicateRecord:
    field: str
    value: Any
    row_numbers: list[int]
    sheet: str


@dataclass
class DuplicateReport:
    total_duplicates: int
    records: list[DuplicateRecord]
    sheet_summaries: dict[str, int]

    def to_dict(self) -> dict:
        return {
            "total_duplicates": self.total_duplicates,
            "sheet_summaries": self.sheet_summaries,
            "records": [
                {
                    "sheet": r.sheet,
                    "field": r.field,
                    "value": str(r.value),
                    "row_numbers": r.row_numbers,
                    "count": len(r.row_numbers),
                }
                for r in self.records
            ],
        }


class DuplicateDetector:
    """Detects duplicate values across key fields in sheet data."""

    # Fields to check per sheet
    KEY_FIELDS = {
        "BPLS-Business": ["bin", "business_name"],
        "BPLS-Business Activity": ["bin"],
        "BPLS-Application": ["business_bin", "or_no"],
        "BPLS-Application Fee": ["application_or_no"],
    }

    def detect_all(self, sheets_data: dict[str, list[dict]]) -> DuplicateReport:
        """Run duplicate detection across all sheets."""
        records = []
        sheet_summaries = {}

        for sheet_name, rows in sheets_data.items():
            key_fields = self.KEY_FIELDS.get(sheet_name, [])
            sheet_duplicates = 0

            for field in key_fields:
                dups = self._find_duplicates(rows, field, sheet_name)
                records.extend(dups)
                sheet_duplicates += len(dups)

            if sheet_duplicates > 0:
                sheet_summaries[sheet_name] = sheet_duplicates

        return DuplicateReport(
            total_duplicates=sum(sheet_summaries.values()),
            records=records,
            sheet_summaries=sheet_summaries,
        )

    def _find_duplicates(
        self, rows: list[dict], field: str, sheet_name: str
    ) -> list[DuplicateRecord]:
        """Find duplicate values in a specific field."""
        value_rows: dict[Any, list[int]] = {}

        for idx, row in enumerate(rows, 2):  # row 2 = first data row (1-indexed)
            value = row.get(field)
            if value is None or str(value).strip() == "":
                continue
            normalized = str(value).strip().lower()
            if normalized not in value_rows:
                value_rows[normalized] = []
            value_rows[normalized].append(idx)

        results = []
        for value, row_nums in value_rows.items():
            if len(row_nums) > 1:
                # Get original (non-lowercased) value from first occurrence
                original = rows[row_nums[0] - 2].get(field, value)
                results.append(
                    DuplicateRecord(
                        field=field,
                        value=original,
                        row_numbers=row_nums,
                        sheet=sheet_name,
                    )
                )

        return results

    def generate_csv_report(self, report: DuplicateReport, output_path: str) -> str:
        """Write duplicate report to CSV."""
        import csv

        with open(output_path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(["sheet", "field", "value", "row_numbers", "count"])
            for r in report.records:
                writer.writerow(
                    [
                        r.sheet,
                        r.field,
                        r.value,
                        "; ".join(str(x) for x in r.row_numbers),
                        len(r.row_numbers),
                    ]
                )

        return output_path
