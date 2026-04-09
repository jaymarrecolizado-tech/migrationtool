"""
Historical Tracking — Track error trends across multiple file uploads.
"""

import json
import os
from datetime import datetime
from dataclasses import dataclass, field


@dataclass
class ProcessingRun:
    run_id: str
    timestamp: str
    filename: str
    sheets_processed: int
    total_rows: int
    total_errors: int
    total_warnings: int
    total_corrections: int
    quality_score: float
    sheet_details: dict = field(default_factory=dict)
    processing_time_ms: int = 0

    def to_dict(self) -> dict:
        return {
            "run_id": self.run_id,
            "timestamp": self.timestamp,
            "filename": self.filename,
            "sheets_processed": self.sheets_processed,
            "total_rows": self.total_rows,
            "total_errors": self.total_errors,
            "total_warnings": self.total_warnings,
            "total_corrections": self.total_corrections,
            "quality_score": round(self.quality_score, 1),
            "sheet_details": self.sheet_details,
            "processing_time_ms": self.processing_time_ms,
        }


class HistoricalTracker:
    """Tracks processing history and error trends over time."""

    def __init__(self, history_file: str = "outputs/processing_history.json"):
        self.history_file = history_file
        os.makedirs(os.path.dirname(history_file) or ".", exist_ok=True)

    def record_run(self, run: ProcessingRun):
        """Record a processing run."""
        history = self.load_history()
        history.append(run.to_dict())
        self._save_history(history)

    def load_history(self) -> list[dict]:
        """Load processing history."""
        if os.path.exists(self.history_file):
            with open(self.history_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return []

    def _save_history(self, history: list[dict]):
        """Save processing history."""
        with open(self.history_file, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2)

    def get_trends(self, last_n: int = 20) -> dict:
        """Get error trends over the last N runs."""
        history = self.load_history()
        recent = history[-last_n:]

        if not recent:
            return {"message": "No history available"}

        return {
            "total_runs": len(history),
            "recent_runs": last_n,
            "runs": [
                {
                    "timestamp": r["timestamp"],
                    "filename": r["filename"],
                    "total_rows": r["total_rows"],
                    "total_errors": r["total_errors"],
                    "total_warnings": r["total_warnings"],
                    "total_corrections": r["total_corrections"],
                    "quality_score": r["quality_score"],
                }
                for r in recent
            ],
            "averages": {
                "avg_errors": round(sum(r["total_errors"] for r in recent) / len(recent), 1),
                "avg_corrections": round(sum(r["total_corrections"] for r in recent) / len(recent), 1),
                "avg_quality_score": round(sum(r["quality_score"] for r in recent) / len(recent), 1),
            },
            "trend_direction": self._calculate_trend_direction(recent),
        }

    def _calculate_trend_direction(self, runs: list[dict]) -> dict:
        """Determine if quality is improving or degrading."""
        if len(runs) < 3:
            return {"message": "Need at least 3 runs to determine trend"}

        first_half = runs[: len(runs) // 2]
        second_half = runs[len(runs) // 2 :]

        avg_first = sum(r["quality_score"] for r in first_half) / len(first_half)
        avg_second = sum(r["quality_score"] for r in second_half) / len(second_half)

        diff = avg_second - avg_first
        if diff > 2:
            return {"trend": "improving", "change": round(diff, 1)}
        elif diff < -2:
            return {"trend": "degrading", "change": round(diff, 1)}
        else:
            return {"trend": "stable", "change": round(diff, 1)}

    def get_best_run(self) -> dict | None:
        """Get the run with the highest quality score."""
        history = self.load_history()
        if not history:
            return None
        return max(history, key=lambda r: r.get("quality_score", 0))

    def get_worst_run(self) -> dict | None:
        """Get the run with the lowest quality score."""
        history = self.load_history()
        if not history:
            return None
        return min(history, key=lambda r: r.get("quality_score", float("inf")))

    def generate_trend_chart_html(self, output_path: str) -> str:
        """Generate an HTML page with trend charts."""
        trends = self.get_trends()
        if "runs" not in trends:
            return ""

        runs = trends["runs"]
        chart_points = []
        for r in runs:
            chart_points.append({
                "date": r["timestamp"][:10],
                "errors": r["total_errors"],
                "quality": r["quality_score"],
                "corrections": r["total_corrections"],
            })

        # Simple SVG sparkline
        svg = self._generate_svg_chart(chart_points)

        html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Quality Trends</title>
<style>
  body {{ font-family: system-ui, sans-serif; margin: 2rem; background: #f9fafb; }}
  h1 {{ color: #1f2937; }}
  .summary {{ display: flex; gap: 1rem; margin: 1rem 0; }}
  .card {{ background: white; padding: 1rem 1.5rem; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
  .card h3 {{ margin: 0 0 0.5rem; color: #6b7280; font-size: 0.875rem; }}
  .card .value {{ font-size: 1.5rem; font-weight: bold; }}
  table {{ border-collapse: collapse; width: 100%; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.1); margin-top: 1rem; }}
  th {{ background: #1f2937; color: white; padding: 10px 14px; text-align: left; }}
  td {{ padding: 8px 14px; border-bottom: 1px solid #e5e7eb; }}
</style></head><body>
<h1>📈 Quality Trends</h1>
<div class="summary">
  <div class="card"><h3>Total Runs</h3><div class="value">{trends['total_runs']}</div></div>
  <div class="card"><h3>Avg Errors</h3><div class="value">{trends['averages'].get('avg_errors', 'N/A')}</div></div>
  <div class="card"><h3>Avg Quality</h3><div class="value">{trends['averages'].get('avg_quality_score', 'N/A')}</div></div>
  <div class="card"><h3>Trend</h3><div class="value">{trends.get('trend_direction', {}).get('trend', 'N/A')}</div></div>
</div>
{svg}
<table>
  <tr><th>Date</th><th>File</th><th>Rows</th><th>Errors</th><th>Corrections</th><th>Quality</th></tr>
  {''.join(f"<tr><td>{r['timestamp'][:10]}</td><td>{r['filename']}</td><td>{r['total_rows']}</td><td>{r['total_errors']}</td><td>{r['total_corrections']}</td><td>{r['quality_score']}</td></tr>" for r in runs)}
</table>
</body></html>"""

        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)

        return output_path

    def _generate_svg_chart(self, points: list[dict]) -> str:
        """Generate a simple SVG chart from trend data."""
        if not points:
            return ""

        width, height = 800, 200
        padding = 40
        chart_w = width - 2 * padding
        chart_h = height - 2 * padding

        # Quality line (green)
        quality_vals = [p["quality"] for p in points]
        max_q = max(quality_vals) if quality_vals else 100
        min_q = min(quality_vals) if quality_vals else 0
        range_q = max_q - min_q if max_q != min_q else 1

        quality_path = ""
        for i, q in enumerate(quality_vals):
            x = padding + (i / max(len(points) - 1, 1)) * chart_w
            y = padding + chart_h - ((q - min_q) / range_q) * chart_h
            quality_path += f"{'M' if i == 0 else 'L'}{x:.1f},{y:.1f}"

        # Errors line (red, scaled)
        error_vals = [p["errors"] for p in points]
        max_e = max(error_vals) if error_vals else 1
        range_e = max_e if max_e > 0 else 1

        errors_path = ""
        for i, e in enumerate(error_vals):
            x = padding + (i / max(len(points) - 1, 1)) * chart_w
            y = padding + chart_h - (e / range_e) * chart_h
            errors_path += f"{'M' if i == 0 else 'L'}{x:.1f},{y:.1f}"

        return f"""
<h2>Quality Score vs Errors Over Time</h2>
<svg width="{width}" height="{height}" style="background:white; border-radius:8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
  <polyline points="{quality_path}" fill="none" stroke="#22c55e" stroke-width="2"/>
  <polyline points="{errors_path}" fill="none" stroke="#ef4444" stroke-width="2"/>
  <text x="{padding}" y="{height - 5}" font-size="10" fill="#6b7280">Quality (green) | Errors (red)</text>
  <text x="{padding}" y="15" font-size="10" fill="#6b7280">{points[0]['date']}</text>
  <text x="{width - padding - 60}" y="15" font-size="10" fill="#6b7280">{points[-1]['date']}</text>
</svg>"""
