#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BPLS CSV Validator App - Improved Version
Validates and corrects CSV files based on migration rules from Excel.
- Fixed sec_no conditional: CORPORATION not CORPORATION
- Enhanced date parsing: handles month names (Jan, Feb, etc.) and outputs mm/dd/yyyy with leading zeros
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
        
        # Month name mapping for parsing
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
        
        # Track fields that were trimmed
        self.trimmed_fields = []
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

    def _is_conditional_required(self, row: pd.Series, rule: Dict) -> bool:
        field_name = rule["field"]

        if field_name == "dti_no":
            business_type = str(row.get("business_type", "")).strip().upper()
            return business_type == "SOLE PROPRIETORSHIP"

        elif field_name == "dti_registration_expiry_date":
            business_type = str(row.get("business_type", "")).strip().upper()
            return business_type == "SOLE PROPRIETORSHIP"

        elif field_name == "sec_no":
            # FIXED: Changed from "CORPORATION" to "CORPORATION"
            business_type = str(row.get("business_type", "")).strip().upper()
            return business_type in [
                "ONE PERSON CORPORATION",  # Fixed typo
                "PARTNERSHIP",
                "CORPORATION",  # Fixed spelling
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

    def _trim_all_fields(self, row: pd.Series) -> Tuple[dict, List[str]]:
        """
        Trim all whitespace from all string fields in a row.
        Returns (trimmed_row_dict, list_of_fields_trimmed)
        """
        trimmed_row = {}
        trimmed_fields = []
        
        for field_name, value in row.items():
            if pd.isna(value):
                trimmed_row[field_name] = ""
                continue
            
            original_value = str(value)
            trimmed_value = original_value.strip()
            
            if trimmed_value != original_value:
                trimmed_fields.append(
                    f"{field_name}: '{original_value}' -> '{trimmed_value}'"
                )
            
            trimmed_row[field_name] = trimmed_value
        
        return trimmed_row, trimmed_fields

    def _parse_date(self, value: str) -> Optional[Tuple[int, int, int]]:
        """
        Parse date from various formats including:
        - MM/DD/YYYY
        - M/D/YYYY  
        - YYYY-MM-DD
        - Month names (Jan, Feb, Mar, etc.) with DD, YYYY
        """
        if not value.strip():
            return None

        value = value.strip()
        
        # Try standard date formats first
        for fmt in ("%m/%d/%Y", "%m-%d-%Y", "%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
            try:
                date_obj = datetime.strptime(value, fmt)
                return (date_obj.month, date_obj.day, date_obj.year)
            except ValueError:
                continue

        # Try parsing with month names (e.g., "Jan 19 2026", "3/19/2026", "March 19, 2026")
        # Remove apostrophe if present
        if value.startswith("'"):
            value = value[1:].strip()

        # Pattern: month_name day, year or month_name/day/year
        month_pattern = r"^(\d{1,2})[/-\s/]+(\d{1,2})[/-\s/]+(\d{4})$"
        match = re.match(month_pattern, value)
        if match:
            try:
                month = int(match.group(1))
                day = int(match.group(2))
                year = int(match.group(3))
                return (month, day, year)
            except:
                pass

        # Pattern with month names: "Jan 19 2026", "January-19-2026", "3-Jan-2026"
        # Split by delimiters
        parts = re.split(r"[\s/\-]+", value)
        
        if len(parts) >= 3:
            # Try to identify month, day, year from parts
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

    def _validate_date(self, value: str) -> Tuple[bool, str]:
        """
        Enhanced date validation - handles various date formats and outputs mm/dd/yyyy
        """
        if not value.strip():
            return False, "Date field cannot be empty"

        # Try to parse the date
        parsed = self._parse_date(value)
        
        if parsed is None:
            return False, f"Invalid date format: '{value}'. Expected: MM/DD/YYYY or month name (e.g., 'Jan 19 2026')"

        month, day, year = parsed

        # Validate ranges
        if not (1 <= month <= 12):
            return False, f"Invalid month: {month}. Must be 1-12"

        if not (1 <= day <= 31):
            return False, f"Invalid day: {day}. Must be 1-31"

        if year < 1900 or year > 2100:
            return False, f"Invalid year: {year}. Must be 1900-2100"

        return True, self._format_date(month, day, year)

    def _correct_date_format(self, value: str) -> Tuple[str, str]:
        """
        Correct date format to mm/dd/yyyy with leading zeros
        Returns (corrected_value, correction_message)
        """
        parsed = self._parse_date(value)
        
        if parsed is None:
            return value, ""

        month, day, year = parsed
        corrected = self._format_date(month, day, year)
        
        if corrected != value.strip():
            return corrected, f"Date formatted as: {corrected}"
        
        return value, ""

    def _validate_sex(self, value: str) -> Tuple[bool, str]:
        if not value.strip():
            return True, ""
        
        if value.strip().upper() not in ["M", "F"]:
            return False, "Must be M or F"
        return True, ""

    def _validate_email(self, value: str) -> Tuple[bool, str]:
        if not value.strip():
            return True, ""  # Email can be optional

        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_regex, value.strip()):
            return False, "Must be a valid email address"
        return True, ""

    def _validate_cellphone(self, value: str) -> Tuple[bool, str]:
        if not value.strip():
            return True, ""

        cleaned = re.sub(r"[^0-9]", "", value.strip())
        
        # Check if starts with 639 or can be corrected
        if not cleaned.startswith("639"):
            if cleaned.startswith("9") and len(cleaned) == 10:
                return False, "Cellphone must start with 639"
            if len(cleaned) == 10:
                return False, "Cellphone must start with 639"
        
        if len(cleaned) not in [10, 11]:
            return False, "Cellphone must be 10 or 11 digits"
        
        if not cleaned.startswith("639"):
            cleaned = f"639{cleaned}"
        
        if len(cleaned) == 10:
            return True, ""
        
        return False, "Invalid cellphone format"

    def _correct_cellphone(self, value: str) -> str:
        cleaned = re.sub(r"[^0-9]", "", value.strip())
        
        if not cleaned.startswith("639"):
            if cleaned.startswith("9") and len(cleaned) == 10:
                return f"'639{cleaned}'"
            if len(cleaned) == 10:
                return value
        
        if len(cleaned) == 11 and cleaned.startswith("639"):
            return f"'{cleaned}'"
        
        if len(cleaned) == 10 and cleaned.startswith("63"):
            return f"'6{cleaned}'"
        
        return value

    def _validate_format(self, value: str, rule: Dict) -> Tuple[bool, str]:
        format_rule = rule["format"].lower().strip()
        field = rule["field"]

        if not format_rule:
            return True, ""

        return True, ""

    def _correct_format(self, value: str, rule: Dict) -> str:
        format_rule = rule["format"].lower().strip()

        if not format_rule:
            return value

        if rule["field"] == "bin":
            cleaned = re.sub(r"[^0-9]", "", value)
            parts = cleaned.split("-")
            if len(parts) == 3 and all(p.isdigit() for p in parts):
                return f"{parts[0].zfill(7)}-{parts[1].zfill(4)}-{parts[2].zfill(7)}"

        if rule["field"] == "tin_no":
            digits = re.sub(r"\D", "", value)
            if len(digits) == 12:
                return f"{digits[:3]}-{digits[3:6]}-{digits[6:9]}-{digits[9:]}"

        return value

    def validate_csv(self, csv_path: str, output_path: Optional[str] = None) -> bool:
        try:
            df = pd.read_csv(csv_path, dtype=str, keep_default_na=False, na_values=[''])
        except Exception as e:
            print(f"Error reading CSV file: {e}")
            return False

        sheet_name = None
        for sheet in self.rules.keys():
            if "BUSINESS" in sheet.upper():
                sheet_name = sheet
                break

        if not sheet_name:
            print("No BPLS-Business rules found in Excel file")
            return False

        sheet_rules = self.rules[sheet_name]
        
        field_rules = {rule["field"]: rule for rule in sheet_rules}
        
        validated_rows = []
        total_corrected = 0

        for idx, row in df.iterrows():
            row_errors = []
            row_corrections = []
            row_dict = row.to_dict()

            for rule in sheet_rules:
                field_name = rule["field"]
                required = rule.get("required", "")
                value = str(row.get(field_name, "")).strip()

                # Check conditional required
                is_conditional_required = self._is_conditional_required(row, rule)
                is_required = required.upper() == "YES" or is_conditional_required

                # Check required fields
                if is_required and not value:
                    row_errors.append(
                        f"Field '{field_name}' is required but empty"
                    )
                    continue

                if not value:
                    continue

                # Date validation with auto-correction
                if field_name in [
                    "dti_registration_expiry_date",
                    "application_date",
                    "issued_date",
                    "valid_until",
                ]:
                    valid, msg = self._validate_date(value)
                    if not valid:
                        row_errors.append(msg)
                    else:
                        # Check if format correction needed
                        corrected, corr_msg = self._correct_date_format(value)
                        if corr_msg:
                            row_corrections.append(corr_msg)
                            row_dict[field_name] = corrected
                            total_corrected += 1

                elif field_name == "email_address":
                    valid, msg = self._validate_email(value)
                    if not valid:
                        row_errors.append(msg)

                elif field_name == "cellphone_no":
                    valid, msg = self._validate_cellphone(value)
                    if not valid:
                        # Try auto-correction
                        corrected = self._correct_cellphone(value)
                        if corrected != value:
                            row_corrections.append(f"cellphone_no corrected: {value} -> {corrected}")
                            row_dict[field_name] = corrected
                            total_corrected += 1
                        else:
                            row_errors.append(msg)

                elif field_name == "incharge_sex":
                    valid, msg = self._validate_sex(value)
                    if not valid:
                        row_errors.append(msg)

                # Format validation for BIN
                elif field_name == "bin":
                    format_rule = rule.get("format", "")
                    if format_rule:
                        cleaned = re.sub(r"[^0-9]", "", value)
                        parts = cleaned.split("-")
                        if len(parts) == 3 and all(p.isdigit() for p in parts):
                            expected = f"{parts[0].zfill(7)}-{parts[1].zfill(4)}-{parts[2].zfill(7)}"
                            if value != expected:
                                row_corrections.append(
                                    f"bin formatted as: {value} -> {expected}"
                                )
                                row_dict[field_name] = expected
                                total_corrected += 1

            if row_errors:
                self.errors.extend([f"Row {idx + 2}: {err}" for err in row_errors])
            
            if row_corrections:
                self.corrections.extend([f"Row {idx + 2}: {corr}" for corr in row_corrections])

            validated_rows.append(row_dict)

        print("\n" + "=" * 80)
        print("VALIDATION RESULTS")
        print("=" * 80)
        print(f"Total rows processed: {len(df)}")
        print(f"Rows corrected: {total_corrected}")
        print(f"Rows with errors: {len(self.errors)}")
        print(f"Rows with warnings: {len(self.warnings)}")

        if self.errors:
            print("\nERRORS:")
            for err in self.errors:
                print(f"  {err}")

        if self.corrections:
            print("\nCORRECTED FIELDS:")
            for corr in self.corrections[:20]:  # Show first 20
                print(f"  {corr}")
            if len(self.corrections) > 20:
                print(f"  ... and {len(self.corrections) - 20} more corrections")

        if output_path and validated_rows:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            output_df = pd.DataFrame(validated_rows)
            output_df.to_csv(output_path, index=False)
            print(f"\nValidated CSV saved to: {output_path}")

        return len(self.errors) == 0


def main():
    import argparse

    parser = argparse.ArgumentParser(description="BPLS CSV Validator - Improved")
    parser.add_argument("csv_file", help="Path to input CSV file")
    parser.add_argument("-o", "--output", help="Path to output validated CSV file")
    parser.add_argument("-r", "--rules", default="migration rules.xlsx", 
                      help="Path to Excel rules file (default: migration rules.xlsx)")

    args = parser.parse_args()

    validator = BPLSValidator(args.rules)
    success = validator.validate_csv(args.csv_file, args.output)

    if success:
        print("\nValidation PASSED - CSV is ready for migration.")
        exit(0)
    else:
        print("\nValidation FAILED - Please fix errors above.")
        exit(1)


if __name__ == "__main__":
    main()
