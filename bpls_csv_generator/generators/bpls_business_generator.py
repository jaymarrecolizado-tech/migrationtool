"""
BPLS-Business Format Generator
Validates, cleans, and formats BPLS-Business sheet data
"""

import os
import csv
import json
from datetime import datetime
from typing import Dict, List, Tuple, Optional

import pandas as pd

from config.schema import BPLS_BUSINESS_SCHEMA, CONDITIONAL_RULES, FieldType
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
)
from validators.conditional import ConditionalValidator
from cleaners.data_cleaners import DataCleaner
from validators.base import ValidationResult, ValidationResultStatus, Severity


class BPLSBusinessFormatGenerator:
    """Format generator for BPLS-Business sheet"""

    def __init__(self, output_dir: str = "outputs"):
        self.output_dir = output_dir
        self.validation_results: List[ValidationResult] = []
        self.cleaning_log: List[Dict] = []
        self.cleaned_data: List[Dict] = []
        self.original_data: List[Dict] = []

        os.makedirs(output_dir, exist_ok=True)

    def process(self, filepath: str, auto_correct: bool = True) -> Dict:
        """
        Process BPLS-Business sheet

        Args:
            filepath: Path to Excel file
            auto_correct: Whether to auto-correct issues

        Returns:
            Summary dict
        """
        print("\n" + "="*70)
        print("🏢 BPLS-Business Format Generator")
        print("="*70)

        # Step 1: Read data
        print(f"\n📖 Reading data from: {filepath}")
        data = self._read_data(filepath)
        self.original_data = data.copy()
        print(f"  ✓ Loaded {len(data)} rows")

        # Step 2: Clean data
        print("\n🧹 Cleaning and normalizing data...")
        self.cleaned_data, self.cleaning_log = self._clean_data(data)
        print(f"  ✓ Applied {len(self.cleaning_log)} auto-corrections")

        # Step 3: Validate
        print("\n✅ Validating against schema...")
        self.validation_results = self._validate(auto_correct)
        
        errors = sum(1 for r in self.validation_results if r.status == ValidationResultStatus.FAIL)
        warnings = sum(1 for r in self.validation_results if r.severity == Severity.WARNING)
        print(f"  ✓ Found {errors} errors, {warnings} warnings")

        # Step 4: Generate output
        print("\n💾 Generating validated CSV...")
        output_file = self._generate_csv()
        print(f"  ✓ Saved to: {output_file}")

        # Step 5: Generate reports
        print("\n📊 Generating reports...")
        self._generate_reports()
        print(f"  ✓ Reports saved to: {self.output_dir}")

        # Build summary
        summary = {
            "sheet": "BPLS-Business",
            "total_rows": len(self.cleaned_data),
            "total_errors": errors,
            "total_warnings": warnings,
            "total_corrections": len(self.cleaning_log),
            "output_file": output_file,
        }

        print("\n" + "="*70)
        print("✅ BPLS-Business Processing Complete!")
        print("="*70)
        print(f"📊 Total rows: {summary['total_rows']}")
        print(f"❌ Errors: {summary['total_errors']}")
        print(f"⚠️  Warnings: {summary['total_warnings']}")
        print(f"🔧 Auto-corrections: {summary['total_corrections']}")
        print("="*70)

        return summary

    def _read_data(self, filepath: str) -> List[Dict]:
        """Read BPLS-Business sheet from Excel file - auto-detects header row"""
        try:
            from config.schema import BPLS_BUSINESS_SCHEMA
            expected_fields = list(BPLS_BUSINESS_SCHEMA.keys())
            
            # Try header=0 first
            df0 = pd.read_excel(filepath, sheet_name="BPLS-Business", header=0)
            cols0 = [str(c).strip() for c in df0.columns]
            
            # Check if first row has expected field names
            has_fields_0 = sum(1 for f in expected_fields if f in cols0)
            
            # Try header=1 (second row)  
            df1 = pd.read_excel(filepath, sheet_name="BPLS-Business", header=1)
            cols1 = [str(c).strip() for c in df1.columns]
            has_fields_1 = sum(1 for f in expected_fields if f in cols1)
            
            # Use whichever header gives us more matching fields
            if has_fields_1 > has_fields_0:
                df = df1
                print(f"  ✓ Auto-detected header at row 1 (matched {has_fields_1} fields)")
            else:
                df = df0
                print(f"  ✓ Auto-detected header at row 0 (matched {has_fields_0} fields)")
            
            data = df.to_dict(orient="records")
            
            # Keep all rows that have at least the BIN field populated
            cleaned = []
            for row in data:
                if row.get("bin") is not None and str(row.get("bin")).strip() != "":
                    for key in row.keys():
                        val = row[key]
                        if isinstance(val, float) and pd.isna(val):
                            row[key] = None
                        elif hasattr(val, 'isna') and val.isna():
                            row[key] = None
                    cleaned.append(row)
            
            print(f"  ✓ Loaded {len(cleaned)} rows with data")
            return cleaned
        except Exception as e:
            print(f"❌ Error reading Excel file: {e}")
            return []

    def _clean_data(self, data: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
        """Clean and normalize data"""
        cleaner = DataCleaner()
        return cleaner.clean_sheet("BPLS-Business", data)

    def _validate(self, auto_correct: bool) -> List[ValidationResult]:
        """Validate all rows"""
        results = []

        for row_idx, row in enumerate(self.cleaned_data, start=2):
            # Validate each field
            for field_name, field_def in BPLS_BUSINESS_SCHEMA.items():
                if field_name not in row:
                    continue

                value = row[field_name]
                validators = self._get_validators(field_name, field_def)

                for validator in validators:
                    field_results = validator.validate(
                        value=value,
                        row_num=row_idx,
                        row_data=row,
                    )
                    results.extend(field_results)

            # Conditional validations
            cond_results = self._validate_conditionals(row, row_idx)
            results.extend(cond_results)

        # Apply auto-corrections if enabled
        if auto_correct:
            self._apply_corrections(results)

        return results

    def _get_validators(self, field_name: str, field_def) -> List:
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

        return validators

    def _validate_conditionals(self, row: Dict, row_idx: int) -> List[ValidationResult]:
        """Run conditional validations"""
        results = []

        if "BPLS-Business" not in CONDITIONAL_RULES:
            return results

        for rule in CONDITIONAL_RULES["BPLS-Business"]:
            validator = ConditionalValidator(field_name=rule["field"])

            cond_results = validator.validate(
                value=row.get(rule["field"]),
                row_num=row_idx,
                condition=rule["condition"],
                required=rule.get("required", False),
                validation=rule.get("validation"),
                alternative_field=rule.get("alternative_field"),
                row_data=row,
            )
            results.extend(cond_results)

        return results

    def _apply_corrections(self, results: List[ValidationResult]):
        """Apply auto-corrections"""
        for result in results:
            if result.status == ValidationResultStatus.AUTO_CORRECTED and result.corrected_value is not None:
                row_idx = result.row - 2
                if 0 <= row_idx < len(self.cleaned_data):
                    self.cleaned_data[row_idx][result.field] = result.corrected_value

    def _generate_csv(self) -> str:
        """Generate validated CSV file"""
        if not self.cleaned_data:
            return ""

        # Filter out empty rows (rows where all values are None/empty)
        valid_rows = []
        for row in self.cleaned_data:
            # Check if row has at least one non-empty value
            has_data = any(
                v is not None and str(v).strip() != ""
                for v in row.values()
            )
            if has_data:
                valid_rows.append(row)

        if not valid_rows:
            print("  ⚠️  Warning: No valid data rows found")
            return ""

        fieldnames = list(BPLS_BUSINESS_SCHEMA.keys())
        output_file = os.path.join(self.output_dir, "BPLS-Business_validated.csv")

        with open(output_file, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(valid_rows)

        print(f"  ✓ Wrote {len(valid_rows)} valid rows to CSV")
        return output_file

    def _generate_reports(self):
        """Generate report files"""
        # Validation errors CSV
        errors = [r for r in self.validation_results 
                 if r.status == ValidationResultStatus.FAIL or r.severity == Severity.WARNING]
        
        if errors:
            errors_file = os.path.join(self.output_dir, "BPLS-Business_errors.csv")
            with open(errors_file, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.DictWriter(f, fieldnames=[
                    "field", "row", "status", "severity",
                    "message", "original_value", "corrected_value", "suggestion"
                ])
                writer.writeheader()
                for result in errors:
                    writer.writerow(result.to_dict())

        # Transformation log CSV
        if self.cleaning_log:
            cleaning_file = os.path.join(self.output_dir, "BPLS-Business_transformations.csv")
            with open(cleaning_file, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.DictWriter(f, fieldnames=[
                    "row", "field", "original", "cleaned", "action"
                ])
                writer.writeheader()
                for log in self.cleaning_log:
                    writer.writerow({k: log.get(k, "") for k in ["row", "field", "original", "cleaned", "action"]})
