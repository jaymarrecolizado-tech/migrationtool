#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BPLS CSV Validator - Enhanced Web Version
Auto-detects rules based on CSV headers, provides live edit mode, and saves cleansed data.
"""

import re
from datetime import datetime
from typing import Dict, List, Tuple, Any, Optional
from flask import Flask, request, jsonify, send_file
from werkzeug.utils import secure_filename
import pandas as pd
import os
from io import StringIO

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['CLEANSED_FOLDER'] = 'cleansed'

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['CLEANSED_FOLDER'], exist_ok=True)


class EnhancedBPLSValidator:
    def __init__(self, rules_excel_path: str):
        self.rules = self._load_rules_from_excel(rules_excel_path)
        self.errors = []
        self.warnings = []
        self.corrections = []
        
        # Month name mapping
        self.month_names = {
            'jan': 1, 'january': 1,
            'feb': 2, 'february': 2,
            'mar': 3, 'march': 3,
            'apr': 4, 'april': 4,
            'may': 5,
            'jun': 6, 'june': 6,
            'jul': 7, 'july': 7,
            'aug': 8, 'august': 8,
            'sep': 9, 'september': 9,
            'oct': 10, 'october': 10,
            'nov': 11, 'november': 11,
            'dec': 12, 'december': 12
        }
        
        # Header to sheet mapping
        self.header_sheet_map = {
            # Business master data fields
            'bin', 'business_name', 'trade_name', 'business_type', 
            'dti_no', 'dti_registration_expiry_date', 'sec_no', 'cda_no',
            'tin_no', 'email_address', 'cellphone_no', 'telephone_no',
            'incharge_first_name', 'incharge_middle_name', 'incharge_last_name',
            'incharge_extension_name', 'incharge_sex', 'incharge_country_of_citizenship',
            'incharge_street', 'incharge_barangay', 'incharge_municipality', 'incharge_province',
            'office_street', 'office_barangay_code', 'location_owned', 'tdn_no', 'pin_no',
            'lessor_name', 'monthly_rental', 'area',
            'no_of_male_employees', 'no_of_female_employees',
            'no_of_employees_residing_within_the_area', 'no_of_van',
            'no_of_truck', 'no_of_motorcycle', 'activity_type', 'no_of_employees': 'BPLS-Business',
            
            # Business activity fields
            'bin', 'business_line_code', 'capital_amount', 'gross_amount', 
            'gross_amount_essential', 'gross_amount_nonessential', 'retired_date': 'BPLS-Business Activity',
            
            # Application fields
            'business_bin', 'application_type', 'application_date', 'year', 
            'qtr_from', 'qtr_to', 'amount', 'discount', 'surcharge', 
            'interest', 'total', 'issued_date', 'valid_until': 'BPLS-Application',
            
            # Application fee fields
            'business_bin', 'application_or_no', 'code', 'description', 
            'amount', 'discount', 'interest', 'surcharge', 'total', 'qtr_from',
            'qtr_to', 'year', 'type': 'BPLS-Application Fee',
        }

    def _load_rules_from_excel(self, excel_path: str) -> Dict[str, List[Dict]]:
        try:
            df_dict = pd.read_excel(excel_path, sheet_name=None, dtype=str, header=None)
        except Exception as e:
            raise Exception(f"Failed to read Excel file: {e}")

        rules = {}

        for sheet_name, df in df_dict.items():
            if "BPLS" not in sheet_name.upper():
                continue

            header_idx = None
            for idx, row in df.iterrows():
                if pd.notna(row[0]) and "FIELD" in str(row[0]).strip():
                    header_idx = idx
                    break

            if header_idx is None:
                continue

            columns = df.iloc[header_idx].tolist()
            columns = [
                str(col).strip() if pd.notna(col) else f"col_{i}"
                for i, col in enumerate(columns)
            ]

            sheet_rules = []
            for _, row in df.iloc[header_idx + 1:].iterrows():
                if pd.isna(row[0]):
                    continue

                rule = {
                    "field": str(row[0]).strip(),
                    "required": str(row[1]).strip() if pd.notna(row[1]) else "",
                    "guide": str(row[2]).strip() if pd.notna(row[2]) else "",
                    "format": str(row[3]).strip() if pd.notna(row[3]) else "",
                    "sample": str(row[4]).strip() if pd.notna(row[4]) else "",
                }
                sheet_rules.append(rule)

            rules[sheet_name] = sheet_rules

        return rules

    def _detect_sheet_from_headers(self, headers: List[str]) -> Optional[str]:
        """Detect which validation rules sheet to use based on CSV headers"""
        if not headers:
            return None
            
        # Check for unique field markers
        header_lower = [h.lower().strip() for h in headers]
        
        # Score each sheet
        sheet_scores = {}
        for sheet_name in self.header_sheet_map.keys():
            sheet_headers = self.header_sheet_map[sheet_name]
            matches = sum(1 for h in header_lower if h in [sh.lower() for sh in sheet_headers])
            sheet_scores[sheet_name] = matches
        
        # Return sheet with highest match count
        if not sheet_scores:
            return None
            
        best_sheet = max(sheet_scores, key=sheet_scores.get)
        print(f"📊 Detected headers match '{best_sheet}' with {sheet_scores[best_sheet]} fields")
        return best_sheet

    def _trim_all_fields(self, value: str) -> str:
        """Trim all whitespace from value"""
        if pd.isna(value) or value == '':
            return value
        return str(value).strip()

    def _parse_date(self, value: str) -> Optional[Tuple[int, int, int]]:
        """Parse date from various formats"""
        if not value.strip():
            return None

        value = value.strip()

        # Try standard date formats
        for fmt in ("%m/%d/%Y", "%m-%d-%Y", "%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
            try:
                date_obj = datetime.strptime(value, fmt)
                return (date_obj.month, date_obj.day, date_obj.year)
            except ValueError:
                continue

        # Try parsing with month names
        parts = re.split(r"[\s/\-]+", value)
        month = day = year = None

        if len(parts) >= 3:
            for part in parts:
                part_lower = part.lower()
                if part_lower in self.month_names:
                    month = self.month_names[part_lower]
                    # Find day and year from other parts
                    other_parts = [p for p in parts if p.lower() not in self.month_names]
                    for op in other_parts:
                        if len(op) == 4 and op.isdigit():
                            year = int(op)
                        elif len(op) in [1, 2] and op.isdigit() and int(op) <= 31:
                            day = int(op)
                    return (month, day, year)

        return None

    def _format_date(self, month: int, day: int, year: int) -> str:
        """Format date as mm/dd/yyyy with leading zeros"""
        return f"{month:02d}/{day:02d}/{year:04d}"

    def _validate_row(self, row: pd.Series, field_rules: List[Dict]) -> Tuple[bool, Dict[str, str]]:
        """Validate a single row against field rules"""
        row_errors = {}
        row_dict = row.to_dict()

        for rule in field_rules:
            field_name = rule["field"]
            original_value = str(row.get(field_name, ""))
            
            # Trim whitespace
            trimmed_value = self._trim_all_fields(original_value)
            
            # Update row_dict with trimmed value
            row_dict[field_name] = trimmed_value
            
            required = rule.get("required", "")
            is_required = required.upper() == "YES"

            if is_required and not trimmed_value:
                row_errors[field_name] = {
                    "error": f"Field '{field_name}' is required but empty",
                    "rule": f"Required: {rule.get('guide', 'This field is required')}",
                    "original": original_value,
                    "corrected": ""
                }
                continue

            if not trimmed_value:
                continue

            # Validate based on field type
            if field_name == "bin":
                cleaned = re.sub(r"[^0-9]", "", trimmed_value)
                parts = cleaned.split("-")
                if len(parts) == 3 and all(p.isdigit() for p in parts):
                    expected = f"{parts[0].zfill(7)}-{parts[1].zfill(4)}-{parts[2].zfill(7)}"
                    if trimmed_value != expected:
                        row_errors[field_name] = {
                            "error": f"Must be format: PSGC (7digits) - YEAR (4digits) - INCREMENT (7digits)",
                            "rule": rule.get("guide", "Format: PSGC (7digits) - YEAR (4digits) - INCREMENT (7digits)"),
                            "original": original_value,
                            "corrected": expected
                        }
                    else:
                        # Auto-correct
                        row_dict[field_name] = expected

            elif field_name == "business_type":
                valid_values = [
                    "SOLE PROPRIETORSHIP",
                    "ONE PERSON CORPORATION",
                    "PARTNERSHIP",
                    "CORPORATION",
                    "COOPERATIVE"
                ]
                if trimmed_value.upper() not in valid_values:
                    row_errors[field_name] = {
                        "error": f"Must be one of: {', '.join(valid_values)}",
                        "rule": f"Accepted values: {rule.get('guide', 'Fixed values only')}",
                        "original": original_value,
                        "corrected": ""
                    }

            elif field_name in ["dti_no", "sec_no", "cda_no", "tin_no"]:
                # These are validated in conditional logic, skip basic validation here
                pass

            elif field_name == "email_address":
                email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                if not re.match(email_regex, trimmed_value):
                    row_errors[field_name] = {
                        "error": "Must be a valid email address",
                        "rule": "Format: valid@domain.com",
                        "original": original_value,
                        "corrected": ""
                    }

            elif field_name == "cellphone_no":
                cleaned = re.sub(r"[^0-9]", "", trimmed_value)
                
                if not cleaned.startswith("639"):
                    if len(cleaned) == 10:
                        cleaned = f"639{cleaned}"
                        row_dict[field_name] = cleaned
                else:
                    if len(cleaned) not in [10, 11]:
                        row_errors[field_name] = {
                            "error": "Cellphone must be 10 or 11 digits",
                            "rule": "639 + 9 digits (11 total)",
                            "original": original_value,
                            "corrected": ""
                        }

            elif field_name == "dti_registration_expiry_date":
                parsed = self._parse_date(trimmed_value)
                if not parsed:
                    row_errors[field_name] = {
                        "error": f"Invalid date format: '{trimmed_value}'",
                        "rule": "Format: MM/DD/YYYY (e.g., 03/26/2028)",
                        "original": original_value,
                        "corrected": ""
                    }
                else:
                    month, day, year = parsed
                    corrected = self._format_date(month, day, year)
                    row_dict[field_name] = corrected

        has_errors = len(row_errors) > 0
        return (not has_errors, row_dict, row_errors)

    def process_csv(self, csv_path: str) -> Dict:
        """Process entire CSV and return results"""
        try:
            df = pd.read_csv(csv_path, dtype=str, keep_default_na=False, na_values=[''])
        except Exception as e:
            return {
                "error": f"Failed to read CSV: {e}",
                "headers": [],
                "results": []
            }

        headers = df.columns.tolist()
        
        # Auto-detect which rules sheet to use
        sheet_name = self._detect_sheet_from_headers(headers)
        
        if not sheet_name:
            sheet_name = "BPLS-Business"  # Default

        if sheet_name not in self.rules:
            return {
                "error": f"No rules found for sheet: {sheet_name}",
                "headers": headers,
                "results": []
            }

        field_rules = self.rules[sheet_name]
        
        results = []
        for idx, row in df.iterrows():
            is_valid, row_dict, row_errors = self._validate_row(row, field_rules)
            
            for field_name, error_info in row_errors.items():
                results.append({
                    "row": idx + 2,
                    "field": field_name,
                    "error": error_info["error"],
                    "rule": error_info["rule"],
                    "original": error_info["original"],
                    "corrected": error_info["corrected"]
                })

        return {
            "headers": headers,
            "sheet": sheet_name,
            "results": results,
            "total_rows": len(df),
            "errors_count": len(results),
            "cleansed_df": df
        }


# Routes
@app.route('/')
def index():
    return '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>BPLS CSV Validator - Enhanced</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: #f5f5f5;
                color: #333;
                padding: 20px;
            }
            .container {
                max-width: 1200px;
                margin: 0 auto;
                background: white;
                border-radius: 10px;
                box-shadow: 0 4px 20px rgba(0,0,0,0.1);
                padding: 30px;
            }
            h1 {
                text-align: center;
                margin-bottom: 30px;
                color: #2563eb;
            }
            .upload-section {
                border: 2px dashed #ccc;
                padding: 30px;
                border-radius: 8px;
                margin-bottom: 30px;
                background: #fafafa;
            }
            .btn {
                background: #2563eb;
                color: white;
                padding: 12px 30px;
                border: none;
                border-radius: 6px;
                cursor: pointer;
                font-size: 16px;
                font-weight: 600;
                transition: all 0.3s;
                display: inline-block;
            }
            .btn:hover {
                background: #1d5b8c;
                transform: translateY(-2px);
            }
            .btn:disabled {
                background: #ccc;
                cursor: not-allowed;
                transform: none;
            }
            input[type="file"] {
                display: block;
                margin-bottom: 20px;
                padding: 12px;
                border: 2px solid #ddd;
                border-radius: 6px;
                width: 100%;
                box-sizing: border-box;
            }
            .results-section {
                display: none;
                margin-top: 30px;
            }
            .results-table {
                width: 100%;
                border-collapse: collapse;
                margin-top: 20px;
            }
            .results-table th {
                background: #2563eb;
                color: white;
                padding: 12px;
                text-align: left;
            }
            .results-table td {
                padding: 10px;
                border-bottom: 1px solid #eee;
            }
            .results-table tr:hover {
                background: #f9f9f9;
            }
            .error-row {
                background: #fee;
            }
            .error-cell {
                color: #d32f2f;
                font-weight: 500;
            }
            .error-rule {
                color: #666;
                font-size: 12px;
                font-style: italic;
                margin-top: 4px;
            }
            .action-buttons {
                margin-top: 20px;
                display: flex;
                gap: 10px;
            }
            .btn-secondary {
                background: #6c757d;
                color: white;
            }
            .btn-secondary:hover {
                background: #5a6268;
            }
            .stats {
                display: flex;
                gap: 30px;
                margin-top: 20px;
            }
            .stat {
                flex: 1;
                background: #f0f0f0;
                padding: 20px;
                border-radius: 8px;
            }
            .stat-value {
                font-size: 24px;
                font-weight: bold;
            }
            .stat-label {
                font-size: 12px;
                color: #666;
                margin-bottom: 5px;
            }
            .hidden {
                display: none;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📊 BPLS CSV Validator - Enhanced</h1>
            
            <div class="upload-section">
                <h2>📁 Upload Your CSV File</h2>
                <p>The validator will automatically detect which validation rules to apply based on your CSV headers.</p>
                <input type="file" id="csvFile" accept=".csv" onchange="validateFile()">
                <div id="uploadMessage"></div>
            </div>
            
            <div id="resultsSection" class="results-section">
                <h2>📋 Validation Results</h2>
                
                <div class="stats">
                    <div class="stat">
                        <div class="stat-label">Total Rows</div>
                        <div class="stat-value" id="totalRows">-</div>
                    </div>
                    <div class="stat">
                        <div class="stat-label">Errors Found</div>
                        <div class="stat-value" id="errorCount" style="color: #d32f2f;">-</div>
                    </div>
                    <div class="stat">
                        <div class="stat-label">Fields Corrected</div>
                        <div class="stat-value" id="correctedCount">-</div>
                    </div>
                </div>
                
                <div class="action-buttons">
                    <button class="btn btn-secondary" onclick="downloadOriginal()">⬇️ Download Original</button>
                    <button class="btn" onclick="applyCorrections()">✅ Apply Corrections & Download</button>
                    <button class="btn" onclick="downloadCleansed()">📥 Download Cleansed Data</button>
                </div>
                
                <h3>📝 Errors</h3>
                <table class="results-table">
                    <thead>
                        <tr>
                            <th>Row</th>
                            <th>Field</th>
                            <th>Error</th>
                            <th>Rule (Hover for details)</th>
                            <th>Original Value</th>
                            <th>Suggested Correction</th>
                        </tr>
                    </thead>
                    <tbody id="resultsTableBody"></tbody>
                </table>
                
                <h3>✅ Corrected Fields</h3>
                <table class="results-table">
                    <thead>
                        <tr>
                            <th>Row</th>
                            <th>Field</th>
                            <th>Correction</th>
                            <th>Rule</th>
                        </tr>
                    </thead>
                    <tbody id="correctedTableBody"></tbody>
                </table>
            </div>
        </div>
        
        <script>
            let validationResult = null;
            let correctedData = null;
            
            async function validateFile() {
                const fileInput = document.getElementById('csvFile');
                const uploadMessage = document.getElementById('uploadMessage');
                const resultsSection = document.getElementById('resultsSection');
                
                if (!fileInput.files.length) {
                    uploadMessage.textContent = 'Please select a CSV file';
                    uploadMessage.style.color = '#d32f2f';
                    return;
                }
                
                const file = fileInput.files[0];
                uploadMessage.textContent = '⏳ Validating...';
                uploadMessage.style.color = '#2563eb';
                uploadMessage.style.fontWeight = 'bold';
                
                const formData = new FormData();
                formData.append('file', file);
                
                try {
                    const response = await fetch('/api/validate', {
                        method: 'POST',
                        body: formData
                    });
                    
                    validationResult = await response.json();
                    
                    if (validationResult.error) {
                        uploadMessage.textContent = '❌ ' + validationResult.error;
                        uploadMessage.style.color = '#d32f2f';
                        return;
                    }
                    
                    displayResults();
                    uploadMessage.textContent = '✅ Validation complete!';
                    uploadMessage.style.color = '#28a745';
                    
                } catch (error) {
                    uploadMessage.textContent = '❌ Error: ' + error.message;
                    uploadMessage.style.color = '#d32f2f';
                }
            }
            
            function displayResults() {
                const resultsSection = document.getElementById('resultsSection');
                const totalRows = document.getElementById('totalRows');
                const errorCount = document.getElementById('errorCount');
                const correctedCount = document.getElementById('correctedCount');
                const resultsTableBody = document.getElementById('resultsTableBody');
                const correctedTableBody = document.getElementById('correctedTableBody');
                
                resultsSection.style.display = 'block';
                
                totalRows.textContent = validationResult.total_rows;
                errorCount.textContent = validationResult.errors_count;
                correctedCount.textContent = validationResult.corrected_count || 0;
                
                resultsTableBody.innerHTML = '';
                correctedTableBody.innerHTML = '';
                
                if (validationResult.errors.length === 0) {
                    resultsTableBody.innerHTML = '<tr><td colspan="5" style="text-align: center; color: #28a745; padding: 40px;">🎉 No errors found! Your CSV is ready for migration.</td></tr>';
                    errorCount.textContent = '0';
                    errorCount.style.color = '#28a745';
                }
                
                // Group errors by row
                const errorsByRow = {};
                validationResult.errors.forEach(err => {
                    if (!errorsByRow[err.row]) {
                        errorsByRow[err.row] = [];
                    }
                    errorsByRow[err.row].push(err);
                });
                
                Object.keys(errorsByRow).forEach(row => {
                    const errors = errorsByRow[row];
                    
                    const rowClass = errors.length > 1 ? 'error-row' : '';
                    const rowSpan = errors.length > 1 ? `rowspan="${errors.length}"` : '';
                    
                    let html = `<tr class="${rowClass}">
                        <td>${row}</td>
                        <td ${rowSpan}>
                            ${errors.map(e => `
                                <div class="error-cell">${e.error}</div>
                                ${e.rule ? `<div class="error-rule">💡 ${e.rule}</div>` : ''}
                            `).join('')}
                        </td>
                        <td>${errors[0].original}</td>
                        <td>${errors[0].corrected || ''}</td>
                    </tr>`;
                    
                    resultsTableBody.innerHTML += html;
                });
                
                // Show corrected fields
                if (validationResult.corrected_fields && validationResult.corrected_fields.length > 0) {
                    correctedTableBody.innerHTML = validationResult.corrected_fields.map(c => `
                        <tr>
                            <td>${c.row}</td>
                            <td>${c.field}</td>
                            <td style="color: #28a745;">${c.correction}</td>
                            <td>${c.rule}</td>
                        </tr>
                    `).join('');
                }
            }
            
            async function downloadOriginal() {
                const blob = new Blob([validationResult.original_csv], {type: 'text/csv'});
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'original_data.csv';
                a.click();
            }
            
            async function applyCorrections() {
                if (!correctedData) {
                    alert('Please validate the file first');
                    return;
                }
                
                const blob = new Blob([correctedData], {type: 'text/csv'});
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'validated_data.csv';
                a.click();
            }
            
            async function downloadCleansed() {
                if (!correctedData) {
                    alert('Please validate the file first');
                    return;
                }
                
                const blob = new Blob([correctedData], {type: 'text/csv'});
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'cleansed_data.csv';
                a.click();
            }
        </script>
    </body>
    </html>
    '''


@app.route('/api/validate', methods=['POST'])
def validate_api():
    """API endpoint for CSV validation"""
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files['file']
    if not file:
        return jsonify({"error": "No file selected"}), 400

    # Check file extension
    if not file.filename.lower().endswith('.csv'):
        return jsonify({"error": "Please upload a CSV file"}), 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

    file.save(filepath)

    # Validate
    validator = EnhancedBPLSValidator('migration rules.xlsx')
    validation_result = validator.process_csv(filepath)

    if "cleansed_df" not in validation_result:
        return jsonify({"error": "Validation processing error"}), 500

    # Get cleansed CSV as string
    cleansed_csv = validation_result["cleansed_df"].to_csv(index=False)

    # Track corrected fields
    corrected_fields = []
    for err in validation_result["results"]:
        if err["corrected"]:
            corrected_fields.append({
                "row": err["row"],
                "field": err["field"],
                "correction": err["corrected"],
                "rule": err["rule"]
            })

    response_data = {
        "success": True,
        "total_rows": validation_result["total_rows"],
        "errors_count": validation_result["errors_count"],
        "errors": validation_result["results"],
        "corrected_count": len(corrected_fields),
        "corrected_fields": corrected_fields,
        "detected_sheet": validation_result["sheet"],
        "original_csv": cleansed_csv
    }

    return jsonify(response_data)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
