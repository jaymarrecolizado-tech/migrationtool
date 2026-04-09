"""
Error Heat Map — Identify which fields have the most errors across processing runs.
"""

import csv
import json
import os
from collections import defaultdict
from dataclasses import dataclass, field


@dataclass
class FieldHeatData:
    field: str
    sheet: str
    total_errors: int = 0
    total_warnings: int = 0
    total_corrections: int = 0
    error_rate: float = 0.0  # errors / total_rows
    severity_score: float = 0.0  # weighted: errors*3 + warnings*1 + corrections*0.5


class ErrorHeatMap:
    """Tracks and visualizes which fields have the most validation errors."""

    def __init__(self, history_dir: str = "outputs"):
        self.history_dir = history_dir
        os.makedirs(history_dir, exist_ok=True)

    def process_validation_results(
        self,
        sheet_name: str,
        total_rows: int,
        validation_results: list[dict],
    ) -> dict[str, FieldHeatData]:
        """Process validation results and accumulate heat data."""
        heat: dict[str, FieldHeatData] = {}

        for result in validation_results:
            fld = result.get("field", "")
            if not fld:
                continue
            if fld not in heat:
                heat[fld] = FieldHeatData(field=fld, sheet=sheet_name)

            status = result.get("status", "")
            sev = result.get("severity", "")

            if status == "FAIL":
                if sev == "WARNING":
                    heat[fld].total_warnings += 1
                else:
                    heat[fld].total_errors += 1
            elif status == "AUTO_CORRECTED":
                heat[fld].total_corrections += 1

        # Calculate rates
        for fld_data in heat.values():
            fld_data.error_rate = (
                fld_data.total_errors / total_rows if total_rows > 0 else 0
            )
            fld_data.severity_score = (
                fld_data.total_errors * 3
                + fld_data.total_warnings * 1
                + fld_data.total_corrections * 0.5
            )

        return heat

    def save_heat_data(self, heat: dict[str, FieldHeatData], filepath: str):
        """Save heat data to CSV for persistence."""
        with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(
                ["sheet", "field", "total_errors", "total_warnings", "total_corrections", "error_rate", "severity_score"]
            )
            for fld_data in sorted(heat.values(), key=lambda x: x.severity_score, reverse=True):
                writer.writerow(
                    [
                        fld_data.sheet,
                        fld_data.field,
                        fld_data.total_errors,
                        fld_data.total_warnings,
                        fld_data.total_corrections,
                        round(fld_data.error_rate, 4),
                        round(fld_data.severity_score, 2),
                    ]
                )

    def load_cumulative_heat(self, output_dir: str) -> dict[str, FieldHeatData]:
        """Load and aggregate heat data from all previous runs."""
        cumulative: dict[str, FieldHeatData] = {}

        for filename in os.listdir(output_dir):
            if filename.endswith("_heatmap.csv"):
                filepath = os.path.join(output_dir, filename)
                with open(filepath, "r", encoding="utf-8-sig") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        key = f"{row['sheet']}.{row['field']}"
                        if key not in cumulative:
                            cumulative[key] = FieldHeatData(
                                field=row["field"], sheet=row["sheet"]
                            )
                        cumulative[key].total_errors += int(row["total_errors"])
                        cumulative[key].total_warnings += int(row["total_warnings"])
                        cumulative[key].total_corrections += int(row["total_corrections"])
                        cumulative[key].severity_score = (
                            cumulative[key].total_errors * 3
                            + cumulative[key].total_warnings * 1
                            + cumulative[key].total_corrections * 0.5
                        )

        return cumulative

    def generate_html_heatmap(self, heat: dict[str, FieldHeatData], output_path: str) -> str:
        """Generate an HTML heatmap visualization."""
        if not heat:
            return ""

        sorted_data = sorted(heat.values(), key=lambda x: x.severity_score, reverse=True)
        max_score = max(d.severity_score for d in sorted_data) if sorted_data else 1

        rows_html = ""
        for d in sorted_data[:50]:  # top 50
            intensity = d.severity_score / max_score if max_score > 0 else 0
            color = f"rgba(239, 68, 68, {intensity:.2f})"
            rows_html += f"""
<tr>
  <td>{d.sheet}</td>
  <td>{d.field}</td>
  <td>{d.total_errors}</td>
  <td>{d.total_warnings}</td>
  <td>{d.total_corrections}</td>
  <td style="background:{color}; padding:6px 12px; text-align:center;">{d.severity_score:.1f}</td>
</tr>"""

        html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Error Heat Map</title>
<style>
  body {{ font-family: system-ui, sans-serif; margin: 2rem; background: #f9fafb; }}
  h1 {{ color: #1f2937; }}
  table {{ border-collapse: collapse; width: 100%; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
  th {{ background: #1f2937; color: white; padding: 10px 14px; text-align: left; }}
  td {{ padding: 8px 14px; border-bottom: 1px solid #e5e7eb; }}
  tr:hover {{ background: #f3f4f6; }}
</style></head><body>
<h1>🔥 Error Heat Map</h1>
<p>Top {len(sorted_data[:50])} fields by error severity</p>
<table>
  <tr><th>Sheet</th><th>Field</th><th>Errors</th><th>Warnings</th><th>Corrections</th><th>Severity Score</th></tr>
  {rows_html}
</table>
</body></html>"""

        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)

        return output_path
