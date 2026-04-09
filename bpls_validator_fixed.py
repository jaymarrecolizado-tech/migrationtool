#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BPLS CSV Validator App
Validates and corrects CSV files based on migration rules from Excel.
"""

import re
from datetime import datetime
from typing import Dict, List, Tuple, Any, Optional

import pandas as pd
import numpy as np
import os


class BPLSValidator:
    def __init__(self, rules_excel_path: str):
        self.rules = self._load_rules_from_excel(rules_excel_path)
        self.errors = []
        self.warnings = []
        self.corrections = []

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
            for _, row in df.iloc[header_idx + 1 :].iterrows():
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

    def _is_conditional_required(self, row: pd.Series, rule: Dict) -> bool:
        field_name = rule["field"]

        if field_name == "dti_no":
            business_type = str(row.get("business_type", "")).strip().upper()
            return business_type == "SOLE PROPRIETORSHIP"

        elif field_name == "dti_registration_expiry_date":
            business_type = str(row.get("business_type", "")).strip().upper()
            return business_type == "SOLE PROPRIETORSHIP"

        elif field_name == "sec_no":
            business_type = str(row.get("business_type", "")).strip().upper()
            return business_type in [
                "ONE PERSON CORPORATION",
                "PARTNERSHIP",
                "CORPORATION",
            ]

        elif field_name == "cda_no":
            business_type = str(row.get("business_type", "")).strip().upper()
            return business_type == "COOPERATIVE"

        elif field_name == "tdn_no":
            location_owned = str(row.get("location_owned", "")).strip()
            pin_no = str(row.get("pin_no", "")).strip()
            try:
                owned = bool(int(location_owned)) if location_owned else False
                return owned and not pin_no
            except:
                return False

        elif field_name == "pin_no":
            location_owned = str(row.get("location_owned", "")).strip()
            tdn_no = str(row.get("tdn_no", "")).strip()
            try:
                owned = bool(int(location_owned)) if location_owned else False
                return owned and not tdn_no
            except:
                return False

        elif field_name == "lessor_name":
            location_owned = str(row.get("location_owned", "")).strip()
            try:
                owned = bool(int(location_owned)) if location_owned else False
                return not owned
            except:
                return False

        elif field_name == "monthly_rental":
            location_owned = str(row.get("location_owned", "")).strip()
            try:
                owned = bool(int(location_owned)) if location_owned else False
                return not owned
            except:
                return False

        return False

    def _validate_bin(self, value: str) -> Tuple[bool, str]:
        pattern = r"^\d{7}-\d{4}-\d{7}$"
        if not re.match(pattern, value):
            return False, "Must be in format: 0000000-0000-0000000 (7-4-7 digits)"
        return True, ""

    def _validate_business_type(self, value: str) -> Tuple[bool, str]:
        accepted = [
            "SOLE PROPRIETORSHIP",
            "ONE PERSON CORPORATION",
            "PARTNERSHIP",
            "CORPORATION",
            "COOPERATIVE",
        ]
        if value.strip().upper() not in accepted:
            return False, f"Must be one of: {', '.join(accepted)}"
        return True, ""

    def _validate_dti_no(self, value: str, business_type: str) -> Tuple[bool, str]:
        if not value.strip():
            return True, ""
        pattern = r"^\d{4}-\d{7}$"
        if not re.match(pattern, value):
            return False, "Must be in format: YEAR-7DIGITS (e.g., 2024-1234567)"
        return True, ""

    def _validate_sec_no(self, value: str, business_type: str) -> Tuple[bool, str]:
        if not value.strip():
            return True, ""
        pattern = r"^(CS|PN)\d{4}-\d{5,7}$"
        if not re.match(pattern, value):
            return False, "Must be in format: CS/PnYEAR-5TO7DIGITS (e.g., CS2024-12345)"
        return True, ""

    def _validate_cda_no(self, value: str, business_type: str) -> Tuple[bool, str]:
        if not value.strip():
            return True, ""
        pattern = r"^9520-\d{8}$"
        if not re.match(pattern, value):
            return (
                False,
                "Must be in format: 9520-REGION-XXX-XXXX (e.g., 9520-16012345)",
            )
        return True, ""

    def _validate_email(self, value: str) -> Tuple[bool, str]:
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(pattern, value):
            return False, "Must be a valid email address (e.g., user@domain.com)"
        return True, ""

    def _validate_cellphone(self, value: str) -> Tuple[bool, str]:
        cleaned = re.sub(r"\D", "", value)
        if not cleaned.startswith("63") and not cleaned.startswith("9"):
            return False, "Must start with 63 (international) or 9 (domestic)"
        return True, ""

    def _validate_sex(self, value: str) -> Tuple[bool, str]:
        if value.strip().upper() not in ["M", "F"]:
            return False, "Must be M or F"
        return True, ""

    def _validate_date(self, value: str) -> Tuple[bool, str]:
        if not value.strip():
            return False, "Date field cannot be empty"

        if not value.startswith("'"):
            return (
                False,
                "Date must start with an apostrophe (') to preserve leading zero",
            )

        date_str = value[1:].strip()

        try:
            for fmt in ("%m/%d/%Y", "%m-%d-%Y", "%Y-%m-%d"):
                try:
                    date_obj = datetime.strptime(date_str, fmt)
                    break
                except ValueError:
                    continue
            else:
                return False, "Invalid date format. Use MM/DD/YYYY."

            # Check for leading zero in month if month < 10
            month = date_obj.month
            if month < 10:
                # Extract month part from date string
                parts = re.split(r"[-/]", date_str)
                if parts and parts[0].isdigit():
                    month_str = parts[0]
                    if len(month_str) == 1 and int(month_str) == month:
                        return False, "Month must have leading zero (e.g., 03/26/2028)"
        except:
            return False, "Invalid date format"

        return True, ""

    def _validate_format(self, value: str, rule: Dict) -> Tuple[bool, str]:
        format_rule = rule["format"].lower().strip()
        field = rule["field"]

        if not format_rule:
            return True, ""

        # For now, return True for all format rules until specific validation is implemented
        # This is a temporary placeholder
        return True, ""

    def _correct_format(self, value: str, rule: Dict) -> str:
        format_rule = rule["format"].lower().strip()

        if not format_rule:
            return value

        if rule["field"] == "bin":
            cleaned = re.sub(r"[^0-9-]", "", value)
            parts = cleaned.split("-")
            if len(parts) == 3 and all(p.isdigit() for p in parts):
                return f"{parts[0].zfill(7)}-{parts[1].zfill(4)}-{parts[2].zfill(7)}"

        if rule["field"] == "tin_no" and re.match(
            r"^\d{3}-\d{3}-\d{3}-\d{5}$", value.replace("-", "")
        ):
            digits = re.sub(r"\D", "", value)
            if len(digits) == 12:
                return f"{digits[:3]}-{digits[3:6]}-{digits[6:9]}-{digits[9:]}"

        if rule["field"] == "cellphone_no" and value.startswith("639"):
            cleaned = re.sub(r"\D", "", value)
            if len(cleaned) == 12 and cleaned.startswith("63"):
                return f"'{cleaned}'"
            elif len(cleaned) == 10 and cleaned.startswith("9"):
                return f"'63{cleaned}'"

        return value

    def validate_csv(self, csv_path: str, output_path: str = None) -> Dict:
        self.errors = []
        self.warnings = []
        self.corrections = []

        try:
            df = pd.read_csv(csv_path, dtype=str, keep_default_na=False)
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to read CSV file: {e}",
                "errors": [f"File read error: {e}"],
                "warnings": [],
                "corrected_rows": 0,
                "total_rows": 0,
            }

        total_rows = len(df)
        corrected_rows = 0

        for idx, row in df.iterrows():
            row_errors = []
            row_warnings = []
            row_corrections = []

            for sheet_rules in self.rules.values():
                for rule in sheet_rules:
                    field = rule["field"]
                    if field not in df.columns:
                        continue

                    value = str(row[field]) if pd.notna(row[field]) else ""

                    is_required = rule["required"].upper() in ["YES", "Y", "TRUE"]
                    if is_required and not value.strip():
                        row_errors.append(f"Field '{field}' is required but empty")
                        continue

                    if rule["required"].upper() == "CONDITIONAL":
                        if self._is_conditional_required(row, rule):
                            if not value.strip():
                                row_errors.append(
                                    f"Field '{field}' is conditionally required but empty"
                                )

                    if value.strip() and rule["format"]:
                        format_valid, error_msg = self._validate_format(value, rule)
                        if not format_valid:
                            row_errors.append(
                                f"Field '{field}' format error: {error_msg}"
                            )
                        else:
                            corrected = self._correct_format(value, rule)
                            if corrected != value:
                                row_corrections.append(
                                    (field, value, corrected, error_msg)
                                )

                    if field == "bin":
                        valid, msg = self._validate_bin(value)
                        if not valid:
                            row_errors.append(f"Field 'bin' format error: {msg}")

                    elif field == "business_type":
                        valid, msg = self._validate_business_type(value)
                        if not valid:
                            row_errors.append(
                                f"Field 'business_type' format error: {msg}"
                            )

                    elif field == "dti_no":
                        valid, msg = self._validate_dti_no(
                            value, row.get("business_type", "")
                        )
                        if not valid:
                            row_errors.append(f"Field 'dti_no' format error: {msg}")

                    elif field == "sec_no":
                        valid, msg = self._validate_sec_no(
                            value, row.get("business_type", "")
                        )
                        if not valid:
                            row_errors.append(f"Field 'sec_no' format error: {msg}")

                    elif field == "cda_no":
                        valid, msg = self._validate_cda_no(
                            value, row.get("business_type", "")
                        )
                        if not valid:
                            row_errors.append(f"Field 'cda_no' format error: {msg}")

                    elif field == "email_address":
                        valid, msg = self._validate_email(value)
                        if not valid:
                            row_errors.append(
                                f"Field 'email_address' format error: {msg}"
                            )

                    elif field == "cellphone_no":
                        valid, msg = self._validate_cellphone(value)
                        if not valid:
                            row_errors.append(
                                f"Field 'cellphone_no' format error: {msg}"
                            )

                    elif field == "incharge_sex":
                        valid, msg = self._validate_sex(value)
                        if not valid:
                            row_errors.append(
                                f"Field 'incharge_sex' format error: {msg}"
                            )

                    elif field in [
                        "dti_registration_expiry_date",
                        "application_date",
                        "issued_date",
                        "valid_until",
                    ]:
                        valid, msg = self._validate_date(value)
                        if not valid:
                            row_errors.append(
                                f"Field '{field}' date format error: {msg}"
                            )
                        else:
                            # Correct the date format if needed
                            corrected = self._correct_date(value)
                            if corrected != value:
                                row_corrections.append(
                                    (field, value, corrected, "Corrected date format")
                                )
                                row_corrections.append(
                                    (field, value, corrected, "Corrected date format")
                                )

            if row_errors:
                self.errors.append({"row": idx + 2, "errors": row_errors})

            if row_warnings:
                self.warnings.append({"row": idx + 2, "warnings": row_warnings})

            if row_corrections:
                for field, old_val, new_val, reason in row_corrections:
                    row[field] = new_val
                corrected_rows += 1
                self.corrections.append(
                    {"row": idx + 2, "corrections": row_corrections}
                )

        if output_path and corrected_rows > 0:
            df.to_csv(output_path, index=False, encoding="utf-8-sig")

        return {
            "success": len(self.errors) == 0,
            "message": "Validation completed" + (" with errors" if self.errors else ""),
            "errors": self.errors,
            "warnings": self.warnings,
            "corrections": self.corrections,
            "corrected_rows": corrected_rows,
            "total_rows": total_rows,
            "output_file": output_path,
        }


def main():
    import sys
    import argparse

    parser = argparse.ArgumentParser(description="BPLS CSV Validator")
    parser.add_argument("csv_file", help="Path to input CSV file")
    parser.add_argument("-o", "--output", help="Path to output validated CSV file")
    parser.add_argument(
        "-r",
        "--rules",
        default="migration rules.xlsx",
        help="Path to Excel file with validation rules (default: migration rules.xlsx)",
    )

    args = parser.parse_args()

    if not os.path.exists(args.rules):
        print(f"Error: Rules file '{args.rules}' not found.")
        sys.exit(1)

    if not os.path.exists(args.csv_file):
        print(f"Error: CSV file '{args.csv_file}' not found.")
        sys.exit(1)

    validator = BPLSValidator(args.rules)
    print(f"Validating {args.csv_file}...")
    result = validator.validate_csv(args.csv_file, args.output)

    print("\n" + "=" * 80)
    print("VALIDATION RESULTS")
    print("=" * 80)
    print(f"Total rows processed: {result['total_rows']}")
    print(f"Rows corrected: {result['corrected_rows']}")
    print(f"Rows with errors: {len(result['errors'])}")
    print(f"Rows with warnings: {len(result['warnings'])}")
    print()

    if result["errors"]:
        print("ERRORS:")
        for error in result["errors"]:
            print(f"  Row {error['row']}: {'; '.join(error['errors'])}")
        print()

    if result["warnings"]:
        print("WARNINGS:")
        for warning in result["warnings"]:
            print(f"  Row {warning['row']}: {'; '.join(warning['warnings'])}")
        print()

    if result["corrections"]:
        print("CORRECTED FIELDS:")
        for correction in result["corrections"]:
            for field, old_val, new_val, reason in correction["corrections"]:
                print(
                    f"  Row {correction['row']}: {field} changed from '{old_val}' to '{new_val}'"
                )

    print()
    if result["success"]:
        print("Validation PASSED - No critical errors found.")
        if result["output_file"]:
            print(f"Validated CSV saved to: {result['output_file']}")
    else:
        print("Validation FAILED - Please fix the errors above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
