"""
Data Cleaner/Normalizer for BPLS Migration
Auto-fixes common data issues before validation
"""

import re
from datetime import datetime
from typing import Any, Dict, List, Tuple

from config.schema import (
    SHEET_SCHEMAS,
    FieldType,
    FieldDefinition,
)


class DataCleaner:
    """Cleans and normalizes data based on schema rules"""

    def __init__(self):
        self.cleaning_log: List[Dict] = []

    def clean_sheet(self, sheet_name: str, data: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
        """
        Clean all rows in a sheet

        Args:
            sheet_name: Name of the sheet
            data: List of row dicts

        Returns:
            (cleaned_data, cleaning_log)
        """
        if sheet_name not in SHEET_SCHEMAS:
            raise ValueError(f"Unknown sheet: {sheet_name}")

        schema = SHEET_SCHEMAS[sheet_name]
        cleaned_data = []
        self.cleaning_log = []

        for row_idx, row in enumerate(data, start=2):  # Start from 2 (row 1 is header)
            cleaned_row = dict(row)  # Copy row

            for field_name, field_def in schema.items():
                if field_name not in row:
                    continue

                original_value = row[field_name]
                cleaned_value, was_modified = self._clean_field(
                    field_name, field_def, original_value, row
                )

                if was_modified:
                    cleaned_row[field_name] = cleaned_value
                    self.cleaning_log.append({
                        "sheet": sheet_name,
                        "row": row_idx,
                        "field": field_name,
                        "original": str(original_value),
                        "cleaned": str(cleaned_value),
                        "action": "Auto-cleaned",
                    })

            cleaned_data.append(cleaned_row)

        return cleaned_data, self.cleaning_log

    def _clean_field(
        self,
        field_name: str,
        field_def: FieldDefinition,
        value: Any,
        row_data: Dict = None
    ) -> Tuple[Any, bool]:
        """Clean a single field value"""

        if value is None or (isinstance(value, str) and value.strip() == ""):
            return value, False

        cleaned = value
        was_modified = False

        # Apply type-specific cleaning
        if field_def.field_type == FieldType.STRING:
            cleaned, was_modified = self._clean_string(value)

        elif field_def.field_type in (FieldType.NUMBER, FieldType.INTEGER):
            cleaned, was_modified = self._clean_number(value, field_def)

        elif field_def.field_type == FieldType.DATE:
            cleaned, was_modified = self._clean_date(value)

        elif field_def.field_type == FieldType.ENUM:
            cleaned, was_modified = self._clean_enum(value, field_def.enum_values)

        elif field_def.field_type == FieldType.BOOLEAN:
            cleaned, was_modified = self._clean_boolean(value)

        elif field_def.field_type == FieldType.EMAIL:
            cleaned, was_modified = self._clean_email(value)

        elif field_def.field_type == FieldType.PHONE:
            cleaned, was_modified = self._clean_phone(value)

        elif field_def.field_type == FieldType.BIN:
            cleaned, was_modified = self._clean_bin(value)

        # Apply length constraints
        if field_def.max_length and isinstance(cleaned, str):
            if len(cleaned) > field_def.max_length:
                cleaned = cleaned[:field_def.max_length]
                was_modified = True

        return cleaned, was_modified

    def _clean_string(self, value: Any) -> Tuple[str, bool]:
        """Clean string value"""
        str_val = str(value).strip()
        was_modified = str_val != str(value)

        # Remove leading/trailing whitespace
        return str_val, was_modified

    def _clean_number(self, value: Any, field_def: FieldDefinition) -> Tuple[Any, bool]:
        """Clean numeric value"""
        if isinstance(value, (int, float)):
            # Convert float to int if it's a whole number and field expects integer
            if field_def.field_type == FieldType.INTEGER and value == int(value):
                return int(value), True
            return value, False

        try:
            # Remove commas and spaces
            str_val = str(value).replace(",", "").strip()
            num_val = float(str_val)

            if field_def.field_type == FieldType.INTEGER:
                int_val = int(num_val)
                return int_val, True

            return num_val, True
        except (ValueError, TypeError):
            return value, False

    def _clean_date(self, value: Any) -> Tuple[str, bool]:
        """Clean and normalize date to MM/DD/YYYY"""
        if isinstance(value, datetime):
            return value.strftime("%m/%d/%Y"), True

        date_str = str(value).strip()

        # List of possible date formats
        formats = [
            "%m/%d/%Y",      # 01/15/2024
            "%m-%d-%Y",      # 01-15-2024
            "%Y-%m-%d",      # 2024-01-15 (ISO)
            "%d/%m/%Y",      # 15/01/2024 (ambiguous, try if others fail)
            "%B %d, %Y",     # January 15, 2024
            "%b %d, %Y",     # Jan 15, 2024
            "%m/%d/%y",      # 01/15/24
            "%Y/%m/%d",      # 2024/01/15
        ]

        for fmt in formats:
            try:
                parsed = datetime.strptime(date_str, fmt)
                formatted = parsed.strftime("%m/%d/%Y")
                return formatted, formatted != date_str
            except ValueError:
                continue

        # Could not parse, return original
        return date_str, False

    def _clean_enum(self, value: Any, allowed_values: List[str]) -> Tuple[str, bool]:
        """Clean enum value (case normalization)"""
        str_val = str(value).strip()

        # Try exact match first
        if str_val in allowed_values:
            return str_val, False

        # Try case-insensitive match
        for allowed in allowed_values:
            if str_val.upper() == allowed.upper():
                return allowed, True

        # For "Others (Text field)" type values, allow any value that starts with "Others"
        # This handles the "Others (Text field)" pattern from Excel rules
        for allowed in allowed_values:
            if "Others" in allowed and str_val.upper().startswith("OTHERS"):
                return str_val, True

        # No match, return original
        return str_val, False

    def _clean_boolean(self, value: Any) -> Tuple[int, bool]:
        """Clean boolean to 1/0"""
        str_val = str(value).strip().lower()

        true_values = {"1", "true", "yes", "t", "y"}
        false_values = {"0", "false", "no", "f", "n"}

        if str_val in true_values:
            return 1, True
        elif str_val in false_values:
            return 0, True

        # Try numeric
        try:
            num = int(value)
            if num in (0, 1):
                return num, False
        except (ValueError, TypeError):
            pass

        return value, False

    def _clean_email(self, value: Any) -> Tuple[str, bool]:
        """Clean email address"""
        email = str(value).strip().lower()
        was_modified = email != str(value)
        return email, was_modified

    def _clean_phone(self, value: Any) -> Tuple[str, bool]:
        """Clean phone number to Philippine format: 639 + 9 digits (12 chars total)"""
        phone = str(value).strip()

        # Remove formatting characters
        cleaned = phone.replace("-", "").replace(" ", "").replace("'", "").replace("(", "").replace(")", "")

        # Convert 09XXXXXXXXX to 639XXXXXXXXX
        if cleaned.startswith("09") and len(cleaned) == 10:
            cleaned = "639" + cleaned[2:]
            return cleaned, True

        # Convert 09XXXXXXXXXX to 639XXXXXXXXX (11 digits starting with 09)
        if cleaned.startswith("09") and len(cleaned) == 11:
            cleaned = "639" + cleaned[2:]
            return cleaned, True

        # Ensure starts with 639
        if not cleaned.startswith("639") and cleaned.startswith("9") and len(cleaned) == 10:
            cleaned = "639" + cleaned
            return cleaned, True

        return cleaned, cleaned != phone

    def _clean_bin(self, value: Any) -> Tuple[str, bool]:
        """Clean BIN format: PSGC(7)-YEAR(4)-INCREMENT(7)"""
        bin_str = str(value).strip()

        # Check if already in correct format
        if re.match(r'^\d{7}-\d{4}-\d{7}$', bin_str):
            return bin_str, False

        # Try to reconstruct from raw digits
        raw = bin_str.replace("-", "").replace(" ", "")

        if len(raw) == 18 and raw.isdigit():
            formatted = f"{raw[0:7]}-{raw[7:11]}-{raw[11:18]}"
            return formatted, True

        # Try with spaces instead of dashes
        parts = bin_str.split()
        if len(parts) == 3 and all(p.isdigit() for p in parts):
            if len(parts[0]) == 7 and len(parts[1]) == 4 and len(parts[2]) == 7:
                return f"{parts[0]}-{parts[1]}-{parts[2]}", True

        return bin_str, False

    def get_cleaning_summary(self) -> Dict:
        """Get summary of cleaning operations"""
        summary = {
            "total_corrections": len(self.cleaning_log),
            "corrections_by_sheet": {},
            "corrections_by_field": {},
            "corrections_by_action": {},
        }

        for log in self.cleaning_log:
            sheet = log["sheet"]
            field = log["field"]
            action = log["action"]

            summary["corrections_by_sheet"][sheet] = summary["corrections_by_sheet"].get(sheet, 0) + 1
            summary["corrections_by_field"][field] = summary["corrections_by_field"].get(field, 0) + 1
            summary["corrections_by_action"][action] = summary["corrections_by_action"].get(action, 0) + 1

        return summary
