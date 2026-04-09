"""
BPLS CSV Generator - Main Orchestrator
Reads Excel file, validates, cleans, and outputs validated CSVs
"""

import os
import csv
import json
from datetime import datetime
from typing import Dict, List, Tuple, Optional

import pandas as pd

from config.schema import SHEET_SCHEMAS, CONDITIONAL_RULES, CROSS_FIELD_RULES, FieldType
from validators.type_validators import (
    StringValidator,
    NumberValidator,
    IntegerValidator,
    DateValidator,
    EnumValidator,
    BooleanValidator,
    EmailValidator,
    PhoneValidator,
    BinValidator,
    ForeignKeyValidator,
)
from validators.conditional import ConditionalValidator, CrossFieldValidator
from cleaners.data_cleaners import DataCleaner
from generators.cross_sheet_validator import CrossSheetValidator
from validators.base import ValidationResult, ValidationResultStatus, Severity


class BPLSCSVGenerator:
    """Main generator that orchestrates the entire pipeline"""

    def __init__(self, output_dir: str = "outputs"):
        self.output_dir = output_dir
        self.validation_results: Dict[str, List[ValidationResult]] = {}
        self.cleaning_logs: Dict[str, List[Dict]] = {}
        self.cross_sheet_results: List[ValidationResult] = []
        self.cleaned_data: Dict[str, List[Dict]] = {}
        self.original_data: Dict[str, List[Dict]] = {}
        self.detected_sheets: Dict[str, str] = {}  # filename -> schema_name mapping

        os.makedirs(output_dir, exist_ok=True)

    def detect_schema(self, columns: List[str]) -> Optional[str]:
        """
        Auto-detect which schema to apply based on column headers.

        Uses a scoring system: matches columns against each schema's required fields.
        Returns the schema name with the highest match score, or None if no match.
        """
        best_match = None
        best_score = 0

        for schema_name, schema in SHEET_SCHEMAS.items():
            # Count how many required fields are present
            required_fields = [
                name for name, defn in schema.items()
                if defn.required.value == "YES"
            ]
            matches = sum(1 for f in required_fields if f in columns)
            score = matches / len(required_fields) if required_fields else 0

            if score > best_score:
                best_score = score
                best_match = schema_name

        # Only return a match if confidence is above 50%
        if best_score >= 0.5:
            return best_match

        return None

    def process_csv_file(self, filepath: str, auto_correct: bool = True) -> Dict:
        """
        Process a CSV file through the full pipeline with auto-detection.

        Args:
            filepath: Path to CSV file
            auto_correct: Whether to auto-correct issues

        Returns:
            Summary dict
        """
        summary = {
            "input_file": filepath,
            "timestamp": datetime.now().isoformat(),
            "sheets_processed": [],
            "total_rows": 0,
            "total_errors": 0,
            "total_warnings": 0,
            "total_corrections": 0,
            "detected_schema": None,
            "detection_confidence": 0,
        }

        # Step 1: Read CSV file and detect schema
        print(f"📖 Reading CSV file: {filepath}")
        sheets_data = self._read_csv_with_detection(filepath)

        if not sheets_data:
            print("❌ No matching schema found in CSV file.")
            summary["error"] = "No matching schema detected"
            return summary

        # Step 2: Clean data
        print("🧹 Cleaning and normalizing data...")
        for sheet_name, data in sheets_data.items():
            if sheet_name in SHEET_SCHEMAS:
                self.original_data[sheet_name] = data
                cleaned, logs = self._clean_sheet(sheet_name, data)
                self.cleaned_data[sheet_name] = cleaned
                self.cleaning_logs[sheet_name] = logs

        # Step 3: Cross-sheet validation
        print("🔗 Validating cross-sheet references...")
        cross_validator = CrossSheetValidator()
        for sheet_name, data in self.cleaned_data.items():
            cross_validator.load_sheet_data(sheet_name, data)
        self.cross_sheet_results = cross_validator.validate_all()

        # Step 4: Validate each sheet
        print("✅ Validating data against schema...")
        for sheet_name, data in self.cleaned_data.items():
            if sheet_name in SHEET_SCHEMAS:
                print(f"  Processing: {sheet_name} ({len(data)} rows)")
                results = self._validate_sheet(sheet_name, data, auto_correct)
                self.validation_results[sheet_name] = results

                # Apply auto-corrections if enabled
                if auto_correct:
                    data = self._apply_corrections(sheet_name, data, results)
                    self.cleaned_data[sheet_name] = data

        # Step 5: Generate output CSVs
        print("💾 Generating validated CSV files...")
        for sheet_name, data in self.cleaned_data.items():
            if sheet_name in SHEET_SCHEMAS:
                self._write_csv(sheet_name, data)

        # Step 6: Generate reports
        print("📊 Generating validation reports...")
        self._generate_reports()

        # Build summary
        summary["sheets_processed"] = list(self.cleaned_data.keys())
        summary["total_rows"] = sum(len(d) for d in self.cleaned_data.values())
        summary["total_errors"] = sum(
            1 for results in self.validation_results.values()
            for r in results if r.status == ValidationResultStatus.FAIL
        )
        summary["total_warnings"] = sum(
            1 for results in self.validation_results.values()
            for r in results if r.severity == Severity.WARNING
        )
        summary["total_corrections"] = sum(
            len(logs) for logs in self.cleaning_logs.values()
        )

        return summary

    def _read_csv_with_detection(self, filepath: str) -> Dict[str, List[Dict]]:
        """
        Read CSV file, detect schema based on columns, and return data.

        For CSV files, each file is treated as a single sheet.
        The schema is auto-detected by matching column headers against known schemas.
        """
        # Read CSV with pandas
        df = pd.read_csv(filepath, encoding="utf-8-sig")

        # Drop columns that are entirely None/NaN (artifacts from empty Excel columns)
        df = df.dropna(axis=1, how="all")

        columns = list(df.columns)

        # Detect schema
        detected_schema = self.detect_schema(columns)

        if detected_schema is None:
            print(f"  ⚠️  No matching schema found for columns: {columns[:5]}...")
            return {}

        print(f"  🔍 Detected schema: {detected_schema} (confidence: {self._get_detection_confidence(columns, detected_schema):.0%})")
        self.detected_sheets[os.path.basename(filepath)] = detected_schema

        # Convert to list of dicts
        data = df.to_dict(orient="records")

        # Remove rows where all values are NaN
        data = [row for row in data if any(pd.notna(v) for v in row.values())]

        # Convert NaN/NaT to None for cleaner handling
        for row in data:
            for key in row.keys():
                val = row[key]
                if isinstance(val, float) and pd.isna(val):
                    row[key] = None
                elif hasattr(val, 'isna') and val.isna():
                    row[key] = None

        # Normalize column names to match schema keys
        # (CSV headers might have slight variations)
        normalized_data = []
        schema_keys = set(SHEET_SCHEMAS[detected_schema].keys())
        for row in data:
            normalized_row = {}
            for col in row.keys():
                # Try exact match first
                if col in schema_keys:
                    normalized_row[col] = row[col]
                else:
                    # Try case-insensitive match
                    for schema_key in schema_keys:
                        if col.strip().lower() == schema_key.strip().lower():
                            normalized_row[schema_key] = row[col]
                            break
                    else:
                        # Column not in schema, skip
                        pass
            normalized_data.append(normalized_row)

        return {detected_schema: normalized_data}

    def _get_detection_confidence(self, columns: List[str], schema_name: str) -> float:
        """Calculate confidence score for schema detection."""
        if schema_name not in SHEET_SCHEMAS:
            return 0.0

        schema = SHEET_SCHEMAS[schema_name]
        required_fields = [
            name for name, defn in schema.items()
            if defn.required.value == "YES"
        ]
        matches = sum(1 for f in required_fields if f in columns)
        return matches / len(required_fields) if required_fields else 0.0

    def process_excel_file(self, filepath: str, auto_correct: bool = True) -> Dict:
        """
        Process an Excel file through the full pipeline

        Args:
            filepath: Path to Excel file
            auto_correct: Whether to auto-correct issues

        Returns:
            Summary dict
        """
        summary = {
            "input_file": filepath,
            "timestamp": datetime.now().isoformat(),
            "sheets_processed": [],
            "total_rows": 0,
            "total_errors": 0,
            "total_warnings": 0,
            "total_corrections": 0,
        }

        # Step 1: Read Excel file
        print(f"📖 Reading Excel file: {filepath}")
        sheets_data = self._read_excel(filepath)

        # Step 2: Clean data
        print("🧹 Cleaning and normalizing data...")
        for sheet_name, data in sheets_data.items():
            if sheet_name in SHEET_SCHEMAS:
                self.original_data[sheet_name] = data
                cleaned, logs = self._clean_sheet(sheet_name, data)
                self.cleaned_data[sheet_name] = cleaned
                self.cleaning_logs[sheet_name] = logs

        # Step 3: Cross-sheet validation
        print("🔗 Validating cross-sheet references...")
        cross_validator = CrossSheetValidator()
        for sheet_name, data in self.cleaned_data.items():
            cross_validator.load_sheet_data(sheet_name, data)
        self.cross_sheet_results = cross_validator.validate_all()

        # Step 4: Validate each sheet
        print("✅ Validating data against schema...")
        for sheet_name, data in self.cleaned_data.items():
            if sheet_name in SHEET_SCHEMAS:
                print(f"  Processing: {sheet_name} ({len(data)} rows)")
                results = self._validate_sheet(sheet_name, data, auto_correct)
                self.validation_results[sheet_name] = results

                # Apply auto-corrections if enabled
                if auto_correct:
                    data = self._apply_corrections(sheet_name, data, results)
                    self.cleaned_data[sheet_name] = data

        # Step 5: Generate output CSVs
        print("💾 Generating validated CSV files...")
        for sheet_name, data in self.cleaned_data.items():
            if sheet_name in SHEET_SCHEMAS:
                self._write_csv(sheet_name, data)

        # Step 6: Generate reports
        print("📊 Generating validation reports...")
        self._generate_reports()

        # Build summary
        summary["sheets_processed"] = list(self.cleaned_data.keys())
        summary["total_rows"] = sum(len(d) for d in self.cleaned_data.values())
        summary["total_errors"] = sum(
            1 for results in self.validation_results.values()
            for r in results if r.status == ValidationResultStatus.FAIL
        )
        summary["total_warnings"] = sum(
            1 for results in self.validation_results.values()
            for r in results if r.severity == Severity.WARNING
        )
        summary["total_corrections"] = sum(
            len(logs) for logs in self.cleaning_logs.values()
        )

        return summary

    def _read_excel(self, filepath: str) -> Dict[str, List[Dict]]:
        """Read Excel file and return dict of sheet_name -> list of row dicts"""
        sheets_data = {}

        xls = pd.ExcelFile(filepath)

        for sheet_name in xls.sheet_names:
            # Skip non-data sheets
            if sheet_name not in SHEET_SCHEMAS:
                continue

            df = pd.read_excel(xls, sheet_name=sheet_name, header=1)  # Row 2 is header

            # Drop columns that are entirely None/NaN (artifacts from empty Excel columns)
            df = df.dropna(axis=1, how="all")

            # Also drop columns where the header itself is None/NaN
            df = df.loc[:, df.columns.notna()]

            data = df.to_dict(orient="records")

            # Remove rows where all values are NaN
            data = [row for row in data if any(pd.notna(v) for v in row.values())]

            # Convert NaN/NaT to None for cleaner handling
            for row in data:
                for key in row.keys():
                    val = row[key]
                    if isinstance(val, float) and pd.isna(val):
                        row[key] = None
                    elif hasattr(val, 'isna') and val.isna():
                        row[key] = None

            sheets_data[sheet_name] = data
            print(f"  Loaded {sheet_name}: {len(data)} rows")

        return sheets_data

    def _clean_sheet(self, sheet_name: str, data: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
        """Clean and normalize sheet data"""
        cleaner = DataCleaner()
        return cleaner.clean_sheet(sheet_name, data)

    def _validate_sheet(
        self,
        sheet_name: str,
        data: List[Dict],
        auto_correct: bool = True
    ) -> List[ValidationResult]:
        """Validate all rows in a sheet"""
        schema = SHEET_SCHEMAS[sheet_name]
        results = []

        for row_idx, row in enumerate(data, start=2):
            # Validate each field
            for field_name, field_def in schema.items():
                if field_name not in row:
                    continue

                value = row[field_name]
                validators = self._get_validators(field_name, field_def, sheet_name)

                for validator in validators:
                    field_results = validator.validate(
                        value=value,
                        row_num=row_idx,
                        row_data=row,  # For conditional validation
                    )
                    results.extend(field_results)

            # Conditional validations
            cond_results = self._validate_conditionals(sheet_name, row, row_idx)
            results.extend(cond_results)

            # Cross-field validations
            cross_results = self._validate_cross_fields(sheet_name, row, row_idx)
            results.extend(cross_results)

        return results

    def _get_validators(self, field_name: str, field_def, sheet_name: str) -> List:
        """Get appropriate validators for a field"""
        validators = []

        if field_def.field_type == FieldType.STRING:
            validators.append(StringValidator(
                field_name=field_name,
                min_length=field_def.min_length,
                max_length=field_def.max_length,
            ))

        elif field_def.field_type == FieldType.NUMBER:
            validators.append(NumberValidator(
                field_name=field_name,
                min_value=field_def.min_value,
                max_value=field_def.max_value,
            ))

        elif field_def.field_type == FieldType.INTEGER:
            validators.append(IntegerValidator(
                field_name=field_name,
                min_value=field_def.min_value,
                max_value=field_def.max_value,
            ))

        elif field_def.field_type == FieldType.DATE:
            validators.append(DateValidator(field_name=field_name))

        elif field_def.field_type == FieldType.ENUM:
            validators.append(EnumValidator(
                field_name=field_name,
                enum_values=field_def.enum_values,
            ))

        elif field_def.field_type == FieldType.BOOLEAN:
            validators.append(BooleanValidator(field_name=field_name))

        elif field_def.field_type == FieldType.EMAIL:
            validators.append(EmailValidator(field_name=field_name))

        elif field_def.field_type == FieldType.PHONE:
            validators.append(PhoneValidator(field_name=field_name))

        elif field_def.field_type == FieldType.BIN:
            validators.append(BinValidator(field_name=field_name))

        elif field_def.field_type == FieldType.FOREIGN_KEY:
            validators.append(ForeignKeyValidator(
                field_name=field_name,
                parent_sheet=field_def.foreign_key_sheet,
                parent_column=field_def.foreign_key_column,
            ))

        return validators

    def _validate_conditionals(
        self,
        sheet_name: str,
        row: Dict,
        row_idx: int
    ) -> List[ValidationResult]:
        """Run conditional validations for a row"""
        results = []

        if sheet_name not in CONDITIONAL_RULES:
            return results

        for rule in CONDITIONAL_RULES[sheet_name]:
            field_name = rule["field"]
            validator = ConditionalValidator(field_name=field_name)

            cond_results = validator.validate(
                value=row.get(field_name),
                row_num=row_idx,
                condition=rule["condition"],
                required=rule.get("required", False),
                validation=rule.get("validation"),
                alternative_field=rule.get("alternative_field"),
                row_data=row,
            )
            results.extend(cond_results)

        return results

    def _validate_cross_fields(
        self,
        sheet_name: str,
        row: Dict,
        row_idx: int
    ) -> List[ValidationResult]:
        """Run cross-field validations for a row"""
        results = []

        if sheet_name not in CROSS_FIELD_RULES:
            return results

        for rule in CROSS_FIELD_RULES[sheet_name]:
            field = rule["field"]
            validation = rule["validation"]
            message = rule["message"]

            # Evaluate the validation expression
            try:
                # Build a safe evaluation context with row values
                safe_locals = {}
                for key, val in row.items():
                    if val is not None:
                        safe_locals[key] = val

                # For the specific rule: no_of_employees_residing_within_the_area <= no_of_male_employees + no_of_female_employees
                result = eval(validation, {"__builtins__": {}}, safe_locals)
                if not result:
                    results.append(ValidationResult(
                        field=field,
                        row=row_idx,
                        status=ValidationResultStatus.FAIL,
                        severity=Severity.ERROR,
                        message=message,
                        original_value=row.get(field),
                    ))
            except Exception:
                pass  # Skip validation if we can't evaluate

        return results

    def _apply_corrections(
        self,
        sheet_name: str,
        data: List[Dict],
        results: List[ValidationResult]
    ) -> List[Dict]:
        """Apply auto-corrections based on validation results"""
        corrected_data = [dict(row) for row in data]  # Deep copy

        for result in results:
            # Apply corrected_value whenever it exists, regardless of status
            # (PASS with corrected_value means normalization, AUTO_CORRECTED means fix)
            if result.corrected_value is not None:
                row_idx = result.row - 2  # Convert back to 0-based index
                if 0 <= row_idx < len(corrected_data):
                    corrected_data[row_idx][result.field] = result.corrected_value

        return corrected_data

    def _write_csv(self, sheet_name: str, data: List[Dict]):
        """Write validated data to CSV file"""
        if not data:
            return

        # Get schema fields in order
        schema = SHEET_SCHEMAS[sheet_name]
        fieldnames = list(schema.keys())

        # Sanitize filename
        safe_name = sheet_name.replace(" ", "_").replace("/", "_")
        filepath = os.path.join(self.output_dir, f"{safe_name}_validated.csv")

        with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(data)

        print(f"  ✓ {filepath}")

    def _generate_reports(self):
        """Generate all report files"""
        # Validation summary JSON
        summary_path = os.path.join(self.output_dir, "validation_summary.json")
        summary = {
            "timestamp": datetime.now().isoformat(),
            "sheets": {},
        }

        for sheet_name, results in self.validation_results.items():
            sheet_summary = {
                "total_validations": len(results),
                "errors": sum(1 for r in results if r.status == ValidationResultStatus.FAIL),
                "warnings": sum(1 for r in results if r.severity == Severity.WARNING),
                "auto_corrected": sum(1 for r in results if r.status == ValidationResultStatus.AUTO_CORRECTED),
                "passed": sum(1 for r in results if r.status == ValidationResultStatus.PASS),
            }
            summary["sheets"][sheet_name] = sheet_summary

        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, default=str)

        # Detailed validation errors CSV
        errors_path = os.path.join(self.output_dir, "validation_errors.csv")
        all_errors = []
        for sheet_name, results in self.validation_results.items():
            for result in results:
                if result.status == ValidationResultStatus.FAIL or result.severity == Severity.WARNING:
                    error_row = {
                        "sheet": sheet_name,
                        **result.to_dict(),
                    }
                    all_errors.append(error_row)

        if all_errors:
            with open(errors_path, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.DictWriter(f, fieldnames=[
                    "sheet", "field", "row", "status", "severity",
                    "message", "original_value", "corrected_value", "suggestion"
                ])
                writer.writeheader()
                writer.writerows(all_errors)

        # Cleaning log CSV
        cleaning_path = os.path.join(self.output_dir, "transformation_log.csv")
        all_cleaning_logs = []
        for sheet_name, logs in self.cleaning_logs.items():
            for log in logs:
                all_cleaning_logs.append({"sheet": sheet_name, **log})

        if all_cleaning_logs:
            with open(cleaning_path, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.DictWriter(f, fieldnames=[
                    "sheet", "row", "field", "original", "cleaned", "action"
                ])
                writer.writeheader()
                writer.writerows(all_cleaning_logs)

        # Cross-sheet validation errors
        cross_sheet_path = os.path.join(self.output_dir, "cross_sheet_errors.csv")
        if self.cross_sheet_results:
            with open(cross_sheet_path, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.DictWriter(f, fieldnames=[
                    "field", "row", "status", "severity",
                    "message", "original_value", "suggestion"
                ])
                writer.writeheader()
                for result in self.cross_sheet_results:
                    writer.writerow(result.to_dict())

        print(f"  ✓ Reports generated in {self.output_dir}/")
