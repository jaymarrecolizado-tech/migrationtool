"""
PDF Report Generator — Audit-ready PDF reports.
"""

import os
from datetime import datetime


class PDFReportGenerator:
    """Generates audit-ready PDF reports using simple HTML-to-PDF or direct rendering."""

    def __init__(self, output_dir: str = "outputs"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def generate_report(
        self,
        validation_summary: dict,
        sheet_stats: dict,
        quality_scores: dict,
        error_details: list[dict],
        transformation_log: list[dict],
        duplicate_report: dict | None = None,
        filename: str = "migration_report",
    ) -> str:
        """
        Generate an audit-ready PDF report.
        Uses reportlab if available, falls back to HTML.
        """
        try:
            return self._generate_pdf(
                validation_summary, sheet_stats, quality_scores,
                error_details, transformation_log, duplicate_report, filename,
            )
        except ImportError:
            # Fallback to HTML
            return self._generate_html_report(
                validation_summary, sheet_stats, quality_scores,
                error_details, transformation_log, duplicate_report, filename,
            )

    def _generate_pdf(
        self, validation_summary, sheet_stats, quality_scores,
        error_details, transformation_log, duplicate_report, filename,
    ) -> str:
        """Generate a proper PDF using reportlab."""
        from reportlab.lib.pagesizes import letter
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.platypus import (
            SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak,
        )

        output_path = os.path.join(self.output_dir, f"{filename}.pdf")

        doc = SimpleDocTemplate(output_path, pagesize=letter, topMargin=72)
        styles = getSampleStyleSheet()
        story = []

        # Custom styles
        styles.add(ParagraphStyle(
            name="ReportTitle", parent=styles["Title"], fontSize=24, leading=30, spaceAfter=6
        ))
        styles.add(ParagraphStyle(
            name="SectionHeader", parent=styles["Heading2"], fontSize=14, leading=20, spaceBefore=16, spaceAfter=8
        ))

        # Title page
        story.append(Paragraph("BPLS Migration Data Audit Report", styles["ReportTitle"]))
        story.append(Spacer(1, 12))
        story.append(Paragraph(f"Generated: {datetime.now().strftime('%B %d, %Y %H:%M')}", styles["Normal"]))
        story.append(Spacer(1, 24))

        # Executive Summary
        story.append(Paragraph("Executive Summary", styles["SectionHeader"]))
        total_rows = validation_summary.get("total_rows", 0)
        total_errors = validation_summary.get("total_errors", 0)
        total_corrections = validation_summary.get("total_corrections", 0)
        quality = validation_summary.get("overall_quality_score", 0)

        summary_data = [
            ["Metric", "Value"],
            ["Total Rows Processed", str(total_rows)],
            ["Total Validation Errors", str(total_errors)],
            ["Auto-Corrections Applied", str(total_corrections)],
            ["Overall Quality Score", f"{quality:.1f}%"],
        ]
        table = Table(summary_data, colWidths=[250, 200])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4472C4")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 10),
            ("TOPPADDING", (0, 0), (-1, 0), 10),
            ("GRID", (0, 0), (-1, -1), 1, colors.grey),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F2F2F2")]),
        ]))
        story.append(table)
        story.append(PageBreak())

        # Per-Sheet Breakdown
        story.append(Paragraph("Per-Sheet Breakdown", styles["SectionHeader"]))
        for sheet_name, stats in sheet_stats.items():
            story.append(Paragraph(f"<b>{sheet_name}</b>", styles["Heading3"]))
            qs = quality_scores.get(sheet_name, {})
            sheet_table_data = [
                ["Metric", "Value"],
                ["Rows", str(stats.get("total_rows", 0))],
                ["Errors", str(stats.get("total_errors", 0))],
                ["Warnings", str(stats.get("total_warnings", 0))],
                ["Quality Score", f"{qs.get('score', 0):.1f}%"],
            ]
            st = Table(sheet_table_data, colWidths=[200, 200])
            st.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4472C4")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 1, colors.grey),
            ]))
            story.append(st)
            story.append(Spacer(1, 12))

        # Error Details
        story.append(PageBreak())
        story.append(Paragraph("Error Details", styles["SectionHeader"]))
        if error_details:
            error_table_data = [["Sheet", "Field", "Row", "Error", "Suggestion"]]
            for err in error_details[:200]:  # Cap at 200 for PDF size
                error_table_data.append([
                    str(err.get("sheet", "")),
                    str(err.get("field", "")),
                    str(err.get("row", "")),
                    str(err.get("message", ""))[:60],
                    str(err.get("suggestion", ""))[:40],
                ])
            et = Table(error_table_data, colWidths=[80, 80, 40, 180, 120])
            et.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4472C4")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F9F9F9")]),
            ]))
            story.append(et)

        # Footer
        story.append(PageBreak())
        story.append(Paragraph(
            f"Report generated by BPLS CSV Generator on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}. "
            f"This is an automated audit report.",
            styles["Normal"],
        ))

        doc.build(story)
        return output_path

    def _generate_html_report(
        self, validation_summary, sheet_stats, quality_scores,
        error_details, transformation_log, duplicate_report, filename,
    ) -> str:
        """Generate an HTML report (fallback when reportlab is not available)."""
        output_path = os.path.join(self.output_dir, f"{filename}_report.html")

        quality = validation_summary.get("overall_quality_score", 0)
        total_rows = validation_summary.get("total_rows", 0)
        total_errors = validation_summary.get("total_errors", 0)
        total_corrections = validation_summary.get("total_corrections", 0)

        sheet_rows = ""
        for sheet_name, stats in sheet_stats.items():
            qs = quality_scores.get(sheet_name, {})
            sheet_rows += f"""
<tr>
  <td><b>{sheet_name}</b></td>
  <td>{stats.get('total_rows', 0)}</td>
  <td>{stats.get('total_errors', 0)}</td>
  <td>{stats.get('total_warnings', 0)}</td>
  <td>{qs.get('score', 0):.1f}%</td>
</tr>"""

        error_rows = ""
        for err in error_details[:500]:
            error_rows += f"""
<tr>
  <td>{err.get('sheet', '')}</td>
  <td>{err.get('field', '')}</td>
  <td>{err.get('row', '')}</td>
  <td>{err.get('message', '')}</td>
  <td>{err.get('suggestion', '')}</td>
</tr>"""

        html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>BPLS Migration Audit Report</title>
<style>
  body {{ font-family: system-ui, -apple-system, sans-serif; margin: 0; padding: 2rem; background: #f3f4f6; color: #1f2937; }}
  .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 2rem; border-radius: 12px; margin-bottom: 2rem; }}
  .header h1 {{ margin: 0; font-size: 1.8rem; }}
  .header p {{ margin: 0.5rem 0 0; opacity: 0.9; }}
  .summary {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin-bottom: 2rem; }}
  .card {{ background: white; padding: 1.5rem; border-radius: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); text-align: center; }}
  .card h3 {{ margin: 0; color: #6b7280; font-size: 0.875rem; text-transform: uppercase; }}
  .card .value {{ font-size: 2rem; font-weight: bold; margin-top: 0.5rem; }}
  .section {{ background: white; padding: 1.5rem; border-radius: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); margin-bottom: 1.5rem; }}
  .section h2 {{ margin: 0 0 1rem; font-size: 1.25rem; }}
  table {{ width: 100%; border-collapse: collapse; }}
  th {{ background: #1f2937; color: white; padding: 10px 14px; text-align: left; font-size: 0.875rem; }}
  td {{ padding: 8px 14px; border-bottom: 1px solid #e5e7eb; font-size: 0.875rem; }}
  tr:hover {{ background: #f9fafb; }}
  .badge {{ display: inline-block; padding: 2px 8px; border-radius: 999px; font-size: 0.75rem; font-weight: 600; }}
  .badge-green {{ background: #dcfce7; color: #166534; }}
  .badge-red {{ background: #fee2e2; color: #991b1b; }}
  .badge-amber {{ background: #fef3c7; color: #92400e; }}
  @media print {{ body {{ background: white; }} .section {{ box-shadow: none; border: 1px solid #e5e7eb; }} }}
</style></head><body>

<div class="header">
  <h1>📋 BPLS Migration Data Audit Report</h1>
  <p>Generated: {datetime.now().strftime('%B %d, %Y at %H:%M:%S')} | Automated Validation Report</p>
</div>

<div class="summary">
  <div class="card"><h3>Total Rows</h3><div class="value">{total_rows}</div></div>
  <div class="card"><h3>Errors</h3><div class="value" style="color:#ef4444">{total_errors}</div></div>
  <div class="card"><h3>Auto-Corrected</h3><div class="value" style="color:#f59e0b">{total_corrections}</div></div>
  <div class="card"><h3>Quality Score</h3><div class="value" style="color:{'#22c55e' if quality >= 90 else '#f59e0b' if quality >= 70 else '#ef4444'}">{quality:.1f}%</div></div>
</div>

<div class="section">
  <h2>📊 Per-Sheet Summary</h2>
  <table>
    <tr><th>Sheet</th><th>Rows</th><th>Errors</th><th>Warnings</th><th>Quality</th></tr>
    {sheet_rows}
  </table>
</div>

<div class="section">
  <h2>⚠️ Error Details (first 500)</h2>
  <table>
    <tr><th>Sheet</th><th>Field</th><th>Row</th><th>Error</th><th>Suggestion</th></tr>
    {error_rows}
  </table>
</div>

<div class="section">
  <p style="color:#6b7280; font-size:0.875rem;">
    This report was automatically generated by the BPLS CSV Generator. 
    All validation results are based on the schema definitions as of the processing date.
  </p>
</div>

</body></html>"""

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)

        return output_path
