"""
Batch Processor — Process folders of migration files.
"""

import os
import time
from datetime import datetime
from dataclasses import dataclass, field


@dataclass
class BatchResult:
    filename: str
    success: bool
    total_rows: int
    total_errors: int
    total_corrections: int
    quality_score: float
    output_files: list[str] = field(default_factory=list)
    error_message: str = ""
    processing_time_ms: int = 0


@dataclass
class BatchReport:
    total_files: int
    successful: int
    failed: int
    total_rows: int
    total_errors: int
    results: list[BatchResult] = field(default_factory=list)
    start_time: str = ""
    end_time: str = ""

    def to_dict(self) -> dict:
        return {
            "total_files": self.total_files,
            "successful": self.successful,
            "failed": self.failed,
            "total_rows": self.total_rows,
            "total_errors": self.total_errors,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "results": [
                {
                    "filename": r.filename,
                    "success": r.success,
                    "total_rows": r.total_rows,
                    "total_errors": r.total_errors,
                    "quality_score": round(r.quality_score, 1),
                    "processing_time_ms": r.processing_time_ms,
                    "error_message": r.error_message,
                }
                for r in self.results
            ],
        }


class BatchProcessor:
    """Processes multiple migration files from a folder."""

    def __init__(self, output_dir: str = "outputs"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def process_folder(
        self,
        folder_path: str,
        auto_correct: bool = True,
        progress_callback=None,
    ) -> BatchReport:
        """Process all Excel/CSV files in a folder."""
        from generators.csv_generator import BPLSCSVGenerator

        files = [
            f
            for f in os.listdir(folder_path)
            if f.endswith((".xlsx", ".xls", ".csv"))
        ]
        files.sort()

        report = BatchReport(
            total_files=len(files),
            successful=0,
            failed=0,
            total_rows=0,
            total_errors=0,
            start_time=datetime.now().isoformat(),
        )

        for i, filename in enumerate(files):
            filepath = os.path.join(folder_path, filename)
            start = time.time()

            try:
                generator = BPLSCSVGenerator(self.output_dir)
                if filepath.endswith((".xls", ".xlsx")):
                    result = generator.process_excel_file(filepath, auto_correct)
                else:
                    result = generator.process_csv_file(filepath, auto_correct)

                elapsed = int((time.time() - start) * 1000)
                total_rows = sum(r["total_rows"] for r in result.get("sheets", {}).values())
                total_errors = sum(r["total_errors"] for r in result.get("sheets", {}).values())
                total_corrections = sum(r["total_corrections"] for r in result.get("sheets", {}).values())
                total_checks = total_rows * 35  # approximate
                quality = ((total_checks - total_errors) / total_checks * 100) if total_checks > 0 else 100

                batch_result = BatchResult(
                    filename=filename,
                    success=True,
                    total_rows=total_rows,
                    total_errors=total_errors,
                    total_corrections=total_corrections,
                    quality_score=quality,
                    output_files=result.get("generated_files", []),
                    processing_time_ms=elapsed,
                )

                report.successful += 1
                report.total_rows += total_rows
                report.total_errors += total_errors

            except Exception as e:
                elapsed = int((time.time() - start) * 1000)
                batch_result = BatchResult(
                    filename=filename,
                    success=False,
                    total_rows=0,
                    total_errors=0,
                    total_corrections=0,
                    quality_score=0,
                    error_message=str(e),
                    processing_time_ms=elapsed,
                )
                report.failed += 1

            report.results.append(batch_result)

            if progress_callback:
                progress_callback(i + 1, len(files), filename, batch_result.success)

        report.end_time = datetime.now().isoformat()
        return report

    def generate_batch_report_html(self, report: BatchReport, output_path: str) -> str:
        """Generate an HTML batch processing report."""
        rows = ""
        for r in report.results:
            status_icon = "✅" if r.success else "❌"
            rows += f"""
<tr>
  <td>{status_icon}</td>
  <td>{r.filename}</td>
  <td>{r.total_rows}</td>
  <td>{r.total_errors}</td>
  <td>{r.quality_score:.1f}%</td>
  <td>{r.processing_time_ms}ms</td>
  <td>{r.error_message or '—'}</td>
</tr>"""

        html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Batch Processing Report</title>
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
<h1>📦 Batch Processing Report</h1>
<div class="summary">
  <div class="card"><h3>Total Files</h3><div class="value">{report.total_files}</div></div>
  <div class="card"><h3>Successful</h3><div class="value" style="color:#22c55e">{report.successful}</div></div>
  <div class="card"><h3>Failed</h3><div class="value" style="color:#ef4444">{report.failed}</div></div>
  <div class="card"><h3>Total Rows</h3><div class="value">{report.total_rows}</div></div>
</div>
<table>
  <tr><th>Status</th><th>File</th><th>Rows</th><th>Errors</th><th>Quality</th><th>Time</th><th>Error</th></tr>
  {rows}
</table>
</body></html>"""

        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)

        return output_path
