"""
BPLS CSV Generator - Flask Web Application (Enhanced with 24 features)
"""

import os
import sys
import json
import time
import math
import io

# Set stdout to UTF-8 to handle emojis in print statements
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_from_directory, make_response
from werkzeug.utils import secure_filename

from generators.csv_generator import BPLSCSVGenerator
from generators.template_generator import TemplateGenerator
from generators.duplicate_detector import DuplicateDetector
from generators.column_mapper import ColumnMapper
from generators.file_differ import FileDiffer
from generators.quality_dashboard import DataQualityDashboard
from generators.error_heatmap import ErrorHeatMap
from generators.summary_statistics import SummaryStatistics
from generators.historical_tracker import HistoricalTracker, ProcessingRun
from generators.psgc_validator import PSGCValidator
from generators.cross_row_validator import CrossRowValidator
from generators.email_phone_verifier import EmailPhoneVerifier
from generators.webhook_notifier import WebhookNotifier, WebhookConfig, NotificationPayload
from generators.batch_processor import BatchProcessor
from generators.plugin_system import PluginRegistry
from generators.config_profiles import ProfileManager
from generators.pdf_report_generator import PDFReportGenerator


def _sanitize_nan(obj):
    """Recursively replace NaN/Infinity/numpy types with JSON-safe values."""
    # Handle numpy/pandas types
    try:
        import numpy as np
        if isinstance(obj, (np.integer,)):
            return int(obj)
        if isinstance(obj, (np.floating,)):
            val = float(obj)
            if math.isnan(val) or math.isinf(val):
                return None
            return val
        if isinstance(obj, np.ndarray):
            return _sanitize_nan(obj.tolist())
    except ImportError:
        pass

    if isinstance(obj, float) and (math.isnan(obj) or math.isinf(obj)):
        return None
    if isinstance(obj, dict):
        return {k: _sanitize_nan(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_sanitize_nan(item) for item in obj]
    return obj


def safe_jsonify(data, status_code=200):
    """Jsonify with NaN/Infinity sanitization."""
    from flask import jsonify, make_response
    clean_data = _sanitize_nan(data)
    resp = make_response(jsonify(clean_data))
    resp.status_code = status_code
    return resp

# Initialize Flask app
app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024  # 50MB max upload
app.config["UPLOAD_FOLDER"] = os.path.join(os.path.dirname(__file__), "uploads")
app.config["OUTPUT_FOLDER"] = os.path.join(os.path.dirname(__file__), "outputs")

os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
os.makedirs(app.config["OUTPUT_FOLDER"], exist_ok=True)

ALLOWED_EXTENSIONS = {"xlsx", "xls", "csv"}


@app.after_request
def sanitize_json_response(response):
    """Sanitize NaN/Infinity values in JSON responses to prevent JSON parse errors."""
    if response.content_type and "application/json" in response.content_type:
        try:
            import json as _json
            data = response.get_json(silent=True)
            if data is not None:
                clean_data = _sanitize_nan(data)
                response.set_data(_json.dumps(clean_data))
        except Exception:
            pass  # Fall through — don't break responses
    return response

# Initialize services
template_gen = TemplateGenerator(app.config["OUTPUT_FOLDER"])
dup_detector = DuplicateDetector()
column_mapper = ColumnMapper()
file_differ = FileDiffer()
quality_dashboard = DataQualityDashboard()
error_heatmap = ErrorHeatMap(app.config["OUTPUT_FOLDER"])
summary_stats = SummaryStatistics()
historical_tracker = HistoricalTracker(os.path.join(app.config["OUTPUT_FOLDER"], "processing_history.json"))
psgc_validator = PSGCValidator()
cross_row_validator = CrossRowValidator()
email_phone_verifier = EmailPhoneVerifier()
webhook_notifier = WebhookNotifier(os.path.join(app.config["OUTPUT_FOLDER"], "webhook_configs.json"))
batch_processor = BatchProcessor(app.config["OUTPUT_FOLDER"])
plugin_registry = PluginRegistry(os.path.join(os.path.dirname(__file__), "plugins"))
profile_manager = ProfileManager(os.path.join(app.config["OUTPUT_FOLDER"], "profiles.json"))
pdf_generator = PDFReportGenerator(app.config["OUTPUT_FOLDER"])

# Discover plugins on startup
plugin_registry.discover_plugins()


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def _read_excel_data(filepath):
    """Read Excel/CSV file into dict of sheet -> rows."""
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


# ============================================================
# Core Routes
# ============================================================

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/upload", methods=["POST"])
def upload_file():
    """Handle file upload and processing (core pipeline + all new features)."""
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400
    if not allowed_file(file.filename):
        return jsonify({"error": "Invalid file type. Please upload .xlsx, .xls, or .csv file"}), 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(filepath)

    auto_correct = request.form.get("auto_correct", "true").lower() == "true"
    file_ext = filename.rsplit(".", 1)[1].lower()

    start_ms = int(time.time() * 1000)

    try:
        # Apply active profile overrides
        from config.schema import SHEET_SCHEMAS, CONDITIONAL_RULES, CROSS_FIELD_RULES
        active_schemas, active_cond, active_cross = profile_manager.apply_overrides(
            SHEET_SCHEMAS, CONDITIONAL_RULES, CROSS_FIELD_RULES
        )

        # Core processing
        generator = BPLSCSVGenerator(app.config["OUTPUT_FOLDER"])
        if file_ext == "csv":
            summary = generator.process_csv_file(filepath, auto_correct=auto_correct)
        else:
            summary = generator.process_excel_file(filepath, auto_correct=auto_correct)

        elapsed_ms = int(time.time() * 1000) - start_ms

        # Read data for secondary analysis
        sheets_data = _read_excel_data(filepath)

        # Duplicate detection
        dup_report = dup_detector.detect_all(sheets_data)

        # Cross-row validation
        cross_row_issues = []
        for sheet_name, rows in sheets_data.items():
            cross_row_issues.extend(cross_row_validator.validate_all(sheet_name, rows))

        # Email/Phone verification
        email_issues = []
        phone_issues = []
        for sheet_name, rows in sheets_data.items():
            email_issues.extend(email_phone_verifier.verify_sheet_emails(rows))
            phone_issues.extend(email_phone_verifier.verify_sheet_phones(rows))

        # Summary statistics
        stats_report = summary_stats.generate_full_report(sheets_data)

        # Quality scores
        quality_scores = {}
        sheets_summary = summary.get("sheets", {})
        for sheet_name, sheet_data in sheets_summary.items():
            score = quality_dashboard.calculate(sheet_name, sheets_data.get(sheet_name, []), sheet_data.get("validation_results", []))
            quality_scores[sheet_name] = score.to_dict()

        # Error heat map
        for sheet_name, sheet_data in sheets_summary.items():
            heat = error_heatmap.process_validation_results(
                sheet_name, sheet_data.get("total_rows", 0), sheet_data.get("validation_results", [])
            )
            heat_path = os.path.join(app.config["OUTPUT_FOLDER"], f"{sheet_name}_heatmap.csv")
            error_heatmap.save_heat_data(heat, heat_path)

        # Historical tracking
        total_rows = sum(s.get("total_rows", 0) for s in sheets_summary.values())
        total_errors = sum(s.get("total_errors", 0) for s in sheets_summary.values())
        total_corrections = sum(s.get("total_corrections", 0) for s in sheets_summary.values())
        avg_quality = sum(s.get("quality_score", 100) for s in quality_scores.values()) / max(len(quality_scores), 1)

        run = ProcessingRun(
            run_id=datetime.now().strftime("%Y%m%d_%H%M%S"),
            timestamp=datetime.now().isoformat(),
            filename=filename,
            sheets_processed=len(sheets_summary),
            total_rows=total_rows,
            total_errors=total_errors,
            total_warnings=sum(s.get("total_warnings", 0) for s in sheets_summary.values()),
            total_corrections=total_corrections,
            quality_score=avg_quality,
            sheet_details=quality_scores,
            processing_time_ms=elapsed_ms,
        )
        historical_tracker.record_run(run)

        # Webhook notification
        output_files = []
        if os.path.exists(app.config["OUTPUT_FOLDER"]):
            for f in os.listdir(app.config["OUTPUT_FOLDER"]):
                if f.endswith((".csv", ".json", ".html", ".pdf")):
                    output_files.append(f)

        webhook_notifier.notify(NotificationPayload(
            event="BPLS Processing Complete",
            filename=filename,
            total_rows=total_rows,
            total_errors=total_errors,
            total_corrections=total_corrections,
            quality_score=avg_quality,
            output_files=output_files,
        ))

        # Collect all generated files
        generated_files = []
        if os.path.exists(app.config["OUTPUT_FOLDER"]):
            for f in sorted(os.listdir(app.config["OUTPUT_FOLDER"])):
                generated_files.append({
                    "name": f,
                    "url": f"/api/download/{f}",
                    "size": os.path.getsize(os.path.join(app.config["OUTPUT_FOLDER"], f)),
                })

        return jsonify({
            "success": True,
            "summary": summary,
            "duplicates": dup_report.to_dict(),
            "cross_row_issues": [
                {"sheet": i.sheet, "type": i.issue_type, "description": i.description, "rows": i.row_numbers, "severity": i.severity}
                for i in cross_row_issues
            ],
            "email_issues": [{"email": e.email, "valid": e.is_valid_format, "disposable": e.is_disposable, "suggestion": e.suggestion} for e in email_issues],
            "phone_issues": [{"phone": p.phone, "valid": p.is_valid, "carrier": p.carrier, "formatted": p.formatted, "suggestion": p.suggestion} for p in phone_issues],
            "statistics": stats_report,
            "quality_scores": quality_scores,
            "trends": historical_tracker.get_trends(),
            "active_profile": profile_manager.active_profile,
            "files": generated_files,
            "processing_time_ms": elapsed_ms,
        })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/download/<filename>")
def download_file(filename):
    return send_from_directory(app.config["OUTPUT_FOLDER"], filename)


# ============================================================
# Template Generator
# ============================================================

@app.route("/api/templates/generate", methods=["POST"])
def generate_templates():
    """Generate Excel templates for all sheets."""
    data = request.json or {}
    sheet_name = data.get("sheet_name")  # optional — if provided, generate just that one

    try:
        if sheet_name:
            paths = [template_gen.generate_template(sheet_name)]
        else:
            paths = template_gen.generate_all_templates()

        files = [{"name": os.path.basename(p), "url": f"/api/download/{os.path.basename(p)}"} for p in paths]
        return jsonify({"success": True, "files": files})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ============================================================
# Duplicate Detector
# ============================================================

@app.route("/api/duplicates/detect", methods=["POST"])
def detect_duplicates():
    """Detect duplicates in an uploaded file."""
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400
    file = request.files["file"]
    if not allowed_file(file.filename):
        return jsonify({"error": "Invalid file type"}), 400

    filepath = os.path.join(app.config["UPLOAD_FOLDER"], secure_filename(file.filename))
    file.save(filepath)

    try:
        sheets_data = _read_excel_data(filepath)
        report = dup_detector.detect_all(sheets_data)
        output_path = os.path.join(app.config["OUTPUT_FOLDER"], "duplicate_report.csv")
        dup_detector.generate_csv_report(report, output_path)
        return jsonify({"success": True, "report": report.to_dict()})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ============================================================
# Column Mapper
# ============================================================

@app.route("/api/mapping/detect", methods=["POST"])
def detect_column_mapping():
    """Auto-detect column mapping for a source file."""
    data = request.json or {}
    columns = data.get("columns", [])
    target_sheet = data.get("target_sheet", "BPLS-Business")

    try:
        mapping = column_mapper.map_columns(columns, target_sheet)
        sheet_scores = column_mapper.auto_detect_sheet(columns)
        report = column_mapper.generate_mapping_report(columns, target_sheet)
        return jsonify({"success": True, "mapping": mapping, "sheet_scores": sheet_scores, "report": report})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ============================================================
# File Diff
# ============================================================

@app.route("/api/diff/compare", methods=["POST"])
def compare_files():
    """Compare two migration files."""
    if "file_a" not in request.files or "file_b" not in request.files:
        return jsonify({"error": "Two files required"}), 400

    file_a = request.files["file_a"]
    file_b = request.files["file_b"]

    path_a = os.path.join(app.config["UPLOAD_FOLDER"], "diff_a_" + secure_filename(file_a.filename))
    path_b = os.path.join(app.config["UPLOAD_FOLDER"], "diff_b_" + secure_filename(file_b.filename))
    file_a.save(path_a)
    file_b.save(path_b)

    try:
        report = file_differ.compare_files(path_a, path_b)
        output_path = os.path.join(app.config["OUTPUT_FOLDER"], "diff_report.csv")
        file_differ.generate_csv_report(report, output_path)
        return jsonify({"success": True, "report": report.to_dict()})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ============================================================
# Data Quality Dashboard
# ============================================================

@app.route("/api/quality/trends")
def get_quality_trends():
    """Get quality trend data."""
    return jsonify({"success": True, "trends": historical_tracker.get_trends()})


@app.route("/api/quality/trends/chart")
def get_quality_trend_chart():
    """Generate HTML trend chart."""
    output_path = os.path.join(app.config["OUTPUT_FOLDER"], "trends_chart.html")
    path = historical_tracker.generate_trend_chart_html(output_path)
    return jsonify({"success": True, "url": f"/api/download/{os.path.basename(path)}"})


# ============================================================
# Error Heat Map
# ============================================================

@app.route("/api/heatmap/generate")
def generate_heatmap():
    """Generate HTML heatmap visualization."""
    cumulative = error_heatmap.load_cumulative_heat(app.config["OUTPUT_FOLDER"])
    output_path = os.path.join(app.config["OUTPUT_FOLDER"], "heatmap.html")
    path = error_heatmap.generate_html_heatmap(cumulative, output_path)
    return jsonify({"success": True, "url": f"/api/download/{os.path.basename(path)}"})


# ============================================================
# PSGC Validator
# ============================================================

@app.route("/api/psgc/validate", methods=["POST"])
def validate_psgc():
    """Validate a PSGC code."""
    data = request.json or {}
    code = data.get("code", "")
    code_type = data.get("type", "barangay")  # barangay or municipality

    try:
        if code_type == "barangay":
            result = psgc_validator.validate_barangay_code(code)
        else:
            result = psgc_validator.validate_municipality_code(code)
        return jsonify({"success": True, "result": {
            "code": result.code, "is_valid": result.is_valid,
            "region": result.region, "province": result.province,
            "municipality": result.municipality, "barangay": result.barangay,
            "message": result.message,
        }})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ============================================================
# Webhook Config
# ============================================================

@app.route("/api/webhooks", methods=["GET"])
def list_webhooks():
    return jsonify({"success": True, "webhooks": [
        {"name": c.name, "provider": c.provider, "enabled": c.enabled, "url": c.url}
        for c in webhook_notifier.configs
    ]})


@app.route("/api/webhooks", methods=["POST"])
def add_webhook():
    data = request.json or {}
    try:
        config = WebhookConfig(
            url=data["url"],
            provider=data.get("provider", "generic"),
            name=data.get("name", ""),
            enabled=data.get("enabled", True),
        )
        webhook_notifier.add_config(config)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ============================================================
# Batch Processing
# ============================================================

@app.route("/api/batch/process", methods=["POST"])
def batch_process():
    """Process all files in a folder."""
    data = request.json or {}
    folder_path = data.get("folder_path", "")
    auto_correct = data.get("auto_correct", True)

    if not os.path.isdir(folder_path):
        return jsonify({"success": False, "error": "Invalid folder path"}), 400

    try:
        report = batch_processor.process_folder(folder_path, auto_correct)
        report_path = os.path.join(app.config["OUTPUT_FOLDER"], "batch_report.html")
        batch_processor.generate_batch_report_html(report, report_path)
        return jsonify({
            "success": True,
            "report": report.to_dict(),
            "report_url": f"/api/download/{os.path.basename(report_path)}",
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ============================================================
# Plugin System
# ============================================================

@app.route("/api/plugins", methods=["GET"])
def list_plugins():
    return jsonify({"success": True, "plugins": plugin_registry.list_plugins()})


@app.route("/api/plugins/toggle", methods=["POST"])
def toggle_plugin():
    data = request.json or {}
    try:
        plugin_registry.toggle_plugin(data["name"], data.get("enabled", True))
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ============================================================
# Config Profiles
# ============================================================

@app.route("/api/profiles", methods=["GET"])
def list_profiles():
    return jsonify({"success": True, "profiles": profile_manager.list_profiles(), "active": profile_manager.active_profile})


@app.route("/api/profiles", methods=["POST"])
def create_profile():
    data = request.json or {}
    try:
        profile = profile_manager.create_profile(data["name"], data.get("description", ""))
        return jsonify({"success": True, "profile": profile.to_dict()})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/profiles/activate", methods=["POST"])
def activate_profile():
    data = request.json or {}
    try:
        profile_manager.activate(data["name"])
        return jsonify({"success": True, "active": profile_manager.active_profile})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/profiles/deactivate", methods=["POST"])
def deactivate_profile():
    profile_manager.deactivate()
    return jsonify({"success": True, "active": None})


# ============================================================
# PDF Reports
# ============================================================

@app.route("/api/reports/pdf", methods=["POST"])
def generate_pdf_report():
    """Generate a PDF report from the last processing run."""
    data = request.json or {}
    filename = data.get("filename", "bpls_audit_report")

    # Get latest history entry
    history = historical_tracker.load_history()
    if not history:
        return jsonify({"success": False, "error": "No processing history found"}), 400

    latest = history[-1]
    sheet_details = latest.get("sheet_details", {})

    # Build report data
    validation_summary = {
        "total_rows": latest["total_rows"],
        "total_errors": latest["total_errors"],
        "total_corrections": latest["total_corrections"],
        "overall_quality_score": latest["quality_score"],
    }

    sheet_stats = {}
    quality_scores = {}
    for sheet_name, details in sheet_details.items():
        sheet_stats[sheet_name] = {
            "total_rows": details.get("total_rows", 0),
            "total_errors": details.get("total_errors", 0),
            "total_warnings": details.get("total_warnings", 0),
        }
        quality_scores[sheet_name] = {"score": details.get("quality_score", 0)}

    # Read error details from latest error file
    error_details = []
    error_file = os.path.join(app.config["OUTPUT_FOLDER"], "validation_errors.csv")
    if os.path.exists(error_file):
        import csv
        with open(error_file, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                error_details.append(dict(row))

    try:
        output_path = pdf_generator.generate_report(
            validation_summary=validation_summary,
            sheet_stats=sheet_stats,
            quality_scores=quality_scores,
            error_details=error_details,
            transformation_log=[],
            filename=filename,
        )
        return jsonify({
            "success": True,
            "url": f"/api/download/{os.path.basename(output_path)}",
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ============================================================
# Status
# ============================================================

@app.route("/api/status")
def status():
    """API health check + feature listing."""
    return jsonify({
        "status": "ok",
        "features": [
            "template_generator",
            "duplicate_detector",
            "column_mapper",
            "file_differ",
            "quality_dashboard",
            "error_heatmap",
            "summary_statistics",
            "historical_tracking",
            "psgc_validator",
            "cross_row_validator",
            "email_phone_verifier",
            "webhook_notifier",
            "batch_processor",
            "plugin_system",
            "config_profiles",
            "pdf_reports",
            "dark_mode",
            "multi_language",
            "before_after_preview",
        ],
    })


# ============================================================
# Comparison Editor
# ============================================================

@app.route("/api/comparison/<sheet_name>")
def get_comparison_data(sheet_name):
    """Return per-row comparison data with original vs corrected values and validation details."""
    from urllib.parse import unquote
    sheet_name = unquote(sheet_name)
    
    try:
        # Read the uploaded file data
        upload_files = [f for f in os.listdir(app.config["UPLOAD_FOLDER"]) if f.endswith((".xlsx", ".xls", ".csv"))]
        if not upload_files:
            return jsonify({"success": False, "error": "No uploaded file found"}), 404
        
        latest_file = max(upload_files, key=lambda f: os.path.getmtime(os.path.join(app.config["UPLOAD_FOLDER"], f)))
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], latest_file)
        
        # Read sheet data
        import pandas as pd
        file_ext = latest_file.rsplit(".", 1)[1].lower()
        
        if file_ext == "csv":
            df = pd.read_csv(filepath, encoding="utf-8-sig")
        else:
            # Find the sheet name that matches
            xl = pd.ExcelFile(filepath)
            sheet_match = None
            for s in xl.sheet_names:
                if sheet_name.lower() in s.lower() or s.lower() in sheet_name.lower():
                    sheet_match = s
                    break
            if not sheet_match:
                return jsonify({"success": False, "error": f"Sheet '{sheet_name}' not found in file"}), 404
            df = pd.read_excel(filepath, sheet_name=sheet_match)
        
        # Replace NaN with None
        df = df.where(pd.notnull(df), None)
        rows = df.to_dict("records")
        
        # Read validation errors for this sheet
        errors_path = os.path.join(app.config["OUTPUT_FOLDER"], "validation_errors.csv")
        sheet_errors = []
        if os.path.exists(errors_path):
            errors_df = pd.read_csv(errors_path, encoding="utf-8-sig")
            errors_df = errors_df.where(pd.notnull(errors_df), None)
            sheet_errors = errors_df[errors_df["sheet"] == sheet_name].to_dict("records")
        
        # Read transformation log for this sheet
        trans_path = os.path.join(app.config["OUTPUT_FOLDER"], "transformation_log.csv")
        sheet_transforms = []
        if os.path.exists(trans_path):
            trans_df = pd.read_csv(trans_path, encoding="utf-8-sig")
            trans_df = trans_df.where(pd.notnull(trans_df), None)
            sheet_transforms = trans_df[trans_df["sheet"] == sheet_name].to_dict("records")
        
        # Build per-row comparison data
        from config.schema import SHEET_SCHEMAS
        schema = SHEET_SCHEMAS.get(sheet_name, {})
        
        comparison_data = []
        for idx, row in enumerate(rows):
            row_num = idx + 2  # Excel row number (1-based, +1 for header)
            
            # Find errors for this row
            row_errors = [e for e in sheet_errors if int(e.get("row", 0)) == row_num]
            
            # Find transforms for this row
            row_transforms = [t for t in sheet_transforms if int(t.get("row", 0)) == row_num]
            
            # Build field details
            field_details = {}
            for field_name in row.keys():
                original_val = row.get(field_name)
                
                # Check if this field was transformed
                corrected_val = original_val
                for t in row_transforms:
                    if t.get("field") == field_name:
                        corrected_val = t.get("cleaned")
                        break
                
                # Check if this field has errors
                field_errors = [e for e in row_errors if e.get("field") == field_name]
                
                # Get field schema info
                field_schema = schema.get(field_name, {})
                
                field_details[field_name] = {
                    "original": original_val,
                    "corrected": corrected_val,
                    "has_error": len(field_errors) > 0,
                    "has_transform": original_val != corrected_val,
                    "errors": field_errors,
                    "schema": {
                        "type": str(field_schema.field_type.value) if hasattr(field_schema, 'field_type') else "unknown",
                        "required": str(field_schema.required.value) if hasattr(field_schema, 'required') else "NO",
                    }
                }
            
            comparison_data.append({
                "row_num": row_num,
                "fields": field_details,
                "error_count": len(row_errors),
                "transform_count": len(row_transforms)
            })
        
        return jsonify({
            "success": True,
            "sheet_name": sheet_name,
            "total_rows": len(comparison_data),
            "rows": comparison_data,
            "schema_fields": {name: {
                "type": str(defn.field_type.value) if hasattr(defn, 'field_type') else "unknown",
                "required": str(defn.required.value) if hasattr(defn, 'required') else "NO",
            } for name, defn in schema.items()}
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/comparison/save", methods=["POST"])
def save_comparison_edits():
    """Save edited comparison data back to CSV."""
    try:
        data = request.get_json()
        sheet_name = data.get("sheet_name")
        edited_rows = data.get("rows", [])
        
        if not sheet_name or not edited_rows:
            return jsonify({"success": False, "error": "Missing sheet_name or rows"}), 400
        
        # Build cleaned data from edited rows
        cleaned_data = []
        for row_data in edited_rows:
            row = {}
            for field_name, field_data in row_data.get("fields", {}).items():
                row[field_name] = field_data.get("corrected") or field_data.get("original")
            cleaned_data.append(row)
        
        # Write to CSV
        from config.schema import SHEET_SCHEMAS
        schema = SHEET_SCHEMAS.get(sheet_name, {})
        fieldnames = list(schema.keys()) if schema else list(cleaned_data[0].keys()) if cleaned_data else []
        
        safe_name = sheet_name.replace(" ", "_").replace("/", "_")
        output_path = os.path.join(app.config["OUTPUT_FOLDER"], f"{safe_name}_edited.csv")
        
        import csv
        with open(output_path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(cleaned_data)
        
        return jsonify({
            "success": True,
            "output_path": f"/api/download/{os.path.basename(output_path)}",
            "rows_saved": len(cleaned_data)
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


if __name__ == "__main__":
    print("🚀 Starting BPLS CSV Generator Web Interface (Enhanced)...")
    print("📍 Open http://localhost:5000 in your browser")
    print("✨ 24 new features enabled")
    app.run(debug=True, host="0.0.0.0", port=5000)
