"""
Data Type Validators for BPLS Migration
"""

import re
from datetime import datetime
from typing import Any, List, Tuple

from .base import BaseValidator, ValidationResult, ValidationResultStatus, Severity


class StringValidator(BaseValidator):
    """Validates string fields with length constraints"""

    def __init__(self, field_name: str = "", min_length: int = None, max_length: int = None):
        super().__init__(field_name)
        self.min_length = min_length
        self.max_length = max_length

    def validate(self, value: Any, row_num: int, **kwargs) -> List[ValidationResult]:
        results = []

        if self.is_empty(value):
            results.append(ValidationResult(
                field=self.field_name,
                row=row_num,
                status=ValidationResultStatus.FAIL,
                severity=Severity.ERROR,
                message=f"Field '{self.field_name}' is required but empty",
                original_value=value,
            ))
            return results

        str_value = str(value).strip()

        if self.min_length and len(str_value) < self.min_length:
            results.append(ValidationResult(
                field=self.field_name,
                row=row_num,
                status=ValidationResultStatus.FAIL,
                severity=Severity.ERROR,
                message=f"String length {len(str_value)} is less than minimum {self.min_length}",
                original_value=str_value,
                suggestion=f"Ensure value has at least {self.min_length} characters",
            ))

        if self.max_length and len(str_value) > self.max_length:
            results.append(ValidationResult(
                field=self.field_name,
                row=row_num,
                status=ValidationResultStatus.FAIL,
                severity=Severity.ERROR,
                message=f"String length {len(str_value)} exceeds maximum {self.max_length}",
                original_value=str_value,
                suggestion=f"Truncate to {self.max_length} characters or less",
            ))

        if not results:
            results.append(ValidationResult(
                field=self.field_name,
                row=row_num,
                status=ValidationResultStatus.PASS,
                severity=Severity.INFO,
                message="Valid string",
                original_value=str_value,
            ))

        return results

    def clean(self, value: Any, **kwargs) -> Tuple[Any, bool]:
        if self.is_empty(value):
            return value, False
        cleaned = str(value).strip()
        was_modified = cleaned != str(value)
        return cleaned, was_modified


class NumberValidator(BaseValidator):
    """Validates numeric fields"""

    def __init__(self, field_name: str = "", min_value: float = None, max_value: float = None):
        super().__init__(field_name)
        self.min_value = min_value
        self.max_value = max_value

    def validate(self, value: Any, row_num: int, **kwargs) -> List[ValidationResult]:
        results = []

        if self.is_empty(value):
            results.append(ValidationResult(
                field=self.field_name,
                row=row_num,
                status=ValidationResultStatus.FAIL,
                severity=Severity.ERROR,
                message=f"Field '{self.field_name}' is required but empty",
                original_value=value,
            ))
            return results

        try:
            num_value = float(value)
        except (ValueError, TypeError):
            results.append(ValidationResult(
                field=self.field_name,
                row=row_num,
                status=ValidationResultStatus.FAIL,
                severity=Severity.ERROR,
                message=f"Value '{value}' is not a valid number",
                original_value=value,
                suggestion="Provide a numeric value",
            ))
            return results

        if self.min_value is not None and num_value < self.min_value:
            results.append(ValidationResult(
                field=self.field_name,
                row=row_num,
                status=ValidationResultStatus.FAIL,
                severity=Severity.ERROR,
                message=f"Value {num_value} is less than minimum {self.min_value}",
                original_value=num_value,
                suggestion=f"Value must be >= {self.min_value}",
            ))

        if self.max_value is not None and num_value > self.max_value:
            results.append(ValidationResult(
                field=self.field_name,
                row=row_num,
                status=ValidationResultStatus.FAIL,
                severity=Severity.ERROR,
                message=f"Value {num_value} exceeds maximum {self.max_value}",
                original_value=num_value,
                suggestion=f"Value must be <= {self.max_value}",
            ))

        if not results:
            results.append(ValidationResult(
                field=self.field_name,
                row=row_num,
                status=ValidationResultStatus.PASS,
                severity=Severity.INFO,
                message="Valid number",
                original_value=num_value,
            ))

        return results

    def clean(self, value: Any, **kwargs) -> Tuple[Any, bool]:
        if self.is_empty(value):
            return value, False
        try:
            cleaned = float(value)
            # Convert to int if it's a whole number
            if cleaned == int(cleaned):
                cleaned = int(cleaned)
            was_modified = cleaned != value
            return cleaned, was_modified
        except (ValueError, TypeError):
            return value, False


class IntegerValidator(NumberValidator):
    """Validates integer fields"""

    def clean(self, value: Any, **kwargs) -> Tuple[Any, bool]:
        if self.is_empty(value):
            return value, False
        try:
            cleaned = int(float(value))  # Handle "10.0" -> 10
            was_modified = cleaned != value
            return cleaned, was_modified
        except (ValueError, TypeError):
            return value, False


class DateValidator(BaseValidator):
    """Validates and normalizes date fields to MM/DD/YYYY format"""

    DATE_FORMATS = [
        "%m/%d/%Y",      # 01/15/2024
        "%m-%d-%Y",      # 01-15-2024
        "%Y-%m-%d",      # 2024-01-15 (ISO)
        "%d/%m/%Y",      # 15/01/2024
        "%B %d, %Y",     # January 15, 2024
        "%b %d, %Y",     # Jan 15, 2024
        "%m/%d/%y",      # 01/15/24
    ]

    def __init__(self, field_name: str = "", output_format: str = "%m/%d/%Y"):
        super().__init__(field_name)
        self.output_format = output_format

    def validate(self, value: Any, row_num: int, **kwargs) -> List[ValidationResult]:
        results = []

        if self.is_empty(value):
            results.append(ValidationResult(
                field=self.field_name,
                row=row_num,
                status=ValidationResultStatus.FAIL,
                severity=Severity.ERROR,
                message=f"Field '{self.field_name}' is required but empty",
                original_value=value,
            ))
            return results

        # Check if it's already a datetime object
        if isinstance(value, datetime):
            results.append(ValidationResult(
                field=self.field_name,
                row=row_num,
                status=ValidationResultStatus.PASS,
                severity=Severity.INFO,
                message="Valid date",
                original_value=value.strftime(self.output_format),
            ))
            return results

        # Try to parse string date
        date_str = str(value).strip()
        parsed_date = None

        for fmt in self.DATE_FORMATS:
            try:
                parsed_date = datetime.strptime(date_str, fmt)
                break
            except ValueError:
                continue

        if parsed_date:
            results.append(ValidationResult(
                field=self.field_name,
                row=row_num,
                status=ValidationResultStatus.AUTO_CORRECTED,
                severity=Severity.INFO,
                message=f"Date parsed and formatted to {self.output_format}",
                original_value=date_str,
                corrected_value=parsed_date.strftime(self.output_format),
            ))
        else:
            results.append(ValidationResult(
                field=self.field_name,
                row=row_num,
                status=ValidationResultStatus.FAIL,
                severity=Severity.ERROR,
                message=f"Invalid date format: '{date_str}'",
                original_value=date_str,
                suggestion="Use format MM/DD/YYYY (e.g., 01/15/2024)",
            ))

        return results

    def clean(self, value: Any, **kwargs) -> Tuple[Any, bool]:
        if self.is_empty(value):
            return value, False

        if isinstance(value, datetime):
            return value.strftime(self.output_format), True

        date_str = str(value).strip()

        for fmt in self.DATE_FORMATS:
            try:
                parsed_date = datetime.strptime(date_str, fmt)
                formatted = parsed_date.strftime(self.output_format)
                return formatted, formatted != date_str
            except ValueError:
                continue

        return value, False


class EnumValidator(BaseValidator):
    """Validates fields against a fixed set of allowed values"""

    def __init__(self, field_name: str = "", enum_values: List[str] = None, case_insensitive: bool = True):
        super().__init__(field_name)
        self.enum_values = enum_values or []
        self.case_insensitive = case_insensitive

    def validate(self, value: Any, row_num: int, **kwargs) -> List[ValidationResult]:
        results = []

        if self.is_empty(value):
            results.append(ValidationResult(
                field=self.field_name,
                row=row_num,
                status=ValidationResultStatus.FAIL,
                severity=Severity.ERROR,
                message=f"Field '{self.field_name}' is required but empty",
                original_value=value,
            ))
            return results

        str_value = str(value).strip()
        check_value = str_value.upper() if self.case_insensitive else str_value
        allowed = [v.upper() for v in self.enum_values] if self.case_insensitive else self.enum_values

        if check_value in allowed:
            # Find the original case version
            idx = allowed.index(check_value)
            correct_value = self.enum_values[idx]

            if str_value != correct_value:
                results.append(ValidationResult(
                    field=self.field_name,
                    row=row_num,
                    status=ValidationResultStatus.AUTO_CORRECTED,
                    severity=Severity.INFO,
                    message=f"Case corrected to '{correct_value}'",
                    original_value=str_value,
                    corrected_value=correct_value,
                ))
            else:
                results.append(ValidationResult(
                    field=self.field_name,
                    row=row_num,
                    status=ValidationResultStatus.PASS,
                    severity=Severity.INFO,
                    message="Valid enum value",
                    original_value=str_value,
                ))
        else:
            results.append(ValidationResult(
                field=self.field_name,
                row=row_num,
                status=ValidationResultStatus.FAIL,
                severity=Severity.ERROR,
                message=f"Invalid value '{str_value}'. Must be one of: {', '.join(self.enum_values)}",
                original_value=str_value,
                suggestion=f"Allowed values: {', '.join(self.enum_values)}",
            ))

        return results

    def clean(self, value: Any, **kwargs) -> Tuple[Any, bool]:
        if self.is_empty(value):
            return value, False

        str_value = str(value).strip()
        check_value = str_value.upper() if self.case_insensitive else str_value
        allowed = [v.upper() for v in self.enum_values] if self.case_insensitive else self.enum_values

        if check_value in allowed:
            idx = allowed.index(check_value)
            return self.enum_values[idx], self.enum_values[idx] != str_value

        return value, False


class BooleanValidator(BaseValidator):
    """Validates boolean fields with various input formats"""

    TRUE_VALUES = {"1", "true", "yes", "t", "y"}
    FALSE_VALUES = {"0", "false", "no", "f", "n"}

    def validate(self, value: Any, row_num: int, **kwargs) -> List[ValidationResult]:
        results = []

        if self.is_empty(value):
            results.append(ValidationResult(
                field=self.field_name,
                row=row_num,
                status=ValidationResultStatus.FAIL,
                severity=Severity.ERROR,
                message=f"Field '{self.field_name}' is required but empty",
                original_value=value,
            ))
            return results

        str_value = str(value).strip().lower()

        if str_value in self.TRUE_VALUES or str_value in self.FALSE_VALUES:
            bool_val = 1 if str_value in self.TRUE_VALUES else 0
            results.append(ValidationResult(
                field=self.field_name,
                row=row_num,
                status=ValidationResultStatus.PASS,
                severity=Severity.INFO,
                message="Valid boolean",
                original_value=value,
                corrected_value=bool_val,
            ))
        else:
            results.append(ValidationResult(
                field=self.field_name,
                row=row_num,
                status=ValidationResultStatus.FAIL,
                severity=Severity.ERROR,
                message=f"Invalid boolean value '{value}'",
                original_value=value,
                suggestion="Use 1/0, true/false, or yes/no",
            ))

        return results

    def clean(self, value: Any, **kwargs) -> Tuple[Any, bool]:
        if self.is_empty(value):
            return value, False

        str_value = str(value).strip().lower()

        if str_value in self.TRUE_VALUES:
            return 1, True
        elif str_value in self.FALSE_VALUES:
            return 0, True

        return value, False


class EmailValidator(BaseValidator):
    """Validates email addresses"""

    EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')

    def validate(self, value: Any, row_num: int, **kwargs) -> List[ValidationResult]:
        results = []

        if self.is_empty(value):
            results.append(ValidationResult(
                field=self.field_name,
                row=row_num,
                status=ValidationResultStatus.FAIL,
                severity=Severity.ERROR,
                message=f"Field '{self.field_name}' is required but empty",
                original_value=value,
            ))
            return results

        email = str(value).strip()

        if self.EMAIL_PATTERN.match(email):
            results.append(ValidationResult(
                field=self.field_name,
                row=row_num,
                status=ValidationResultStatus.PASS,
                severity=Severity.INFO,
                message="Valid email",
                original_value=email,
            ))
        else:
            results.append(ValidationResult(
                field=self.field_name,
                row=row_num,
                status=ValidationResultStatus.FAIL,
                severity=Severity.ERROR,
                message=f"Invalid email format: '{email}'",
                original_value=email,
                suggestion="Use format: user@example.com",
            ))

        return results

    def clean(self, value: Any, **kwargs) -> Tuple[Any, bool]:
        if self.is_empty(value):
            return value, False
        cleaned = str(value).strip().lower()
        was_modified = cleaned != str(value)
        return cleaned, was_modified


class PhoneValidator(BaseValidator):
    """Validates phone numbers (Philippine format)"""

    def __init__(self, field_name: str = "", required_prefix: str = "639"):
        super().__init__(field_name)
        self.required_prefix = required_prefix

    def validate(self, value: Any, row_num: int, **kwargs) -> List[ValidationResult]:
        results = []

        if self.is_empty(value):
            results.append(ValidationResult(
                field=self.field_name,
                row=row_num,
                status=ValidationResultStatus.FAIL,
                severity=Severity.ERROR,
                message=f"Field '{self.field_name}' is required but empty",
                original_value=value,
            ))
            return results

        phone = str(value).strip().replace("-", "").replace(" ", "").replace("'", "")

        if not phone.isdigit():
            results.append(ValidationResult(
                field=self.field_name,
                row=row_num,
                status=ValidationResultStatus.FAIL,
                severity=Severity.ERROR,
                message=f"Phone number contains non-numeric characters: '{phone}'",
                original_value=value,
                suggestion="Use only numbers",
            ))
            return results

        if not phone.startswith(self.required_prefix):
            if phone.startswith("09") and len(phone) == 11:
                # Auto-convert 09171234567 to 639171234567
                results.append(ValidationResult(
                    field=self.field_name,
                    row=row_num,
                    status=ValidationResultStatus.AUTO_CORRECTED,
                    severity=Severity.INFO,
                    message="Phone prefix converted from 09 to 639",
                    original_value=value,
                    corrected_value=self.required_prefix + phone[2:],
                ))
            else:
                results.append(ValidationResult(
                    field=self.field_name,
                    row=row_num,
                    status=ValidationResultStatus.FAIL,
                    severity=Severity.ERROR,
                    message=f"Phone must start with '{self.required_prefix}': '{phone}'",
                    original_value=value,
                    suggestion=f"Format: {self.required_prefix}XXXXXXXXX",
                ))
        else:
            results.append(ValidationResult(
                field=self.field_name,
                row=row_num,
                status=ValidationResultStatus.PASS,
                severity=Severity.INFO,
                message="Valid phone number",
                original_value=phone,
            ))

        return results

    def clean(self, value: Any, **kwargs) -> Tuple[Any, bool]:
        if self.is_empty(value):
            return value, False

        phone = str(value).strip().replace("-", "").replace(" ", "").replace("'", "")

        if phone.startswith("09") and len(phone) == 11:
            return self.required_prefix + phone[2:], True

        return phone, phone != str(value)


class BinValidator(BaseValidator):
    """Validates BIN format: PSGC(7)-YEAR(4)-INCREMENT(7)"""

    BIN_PATTERN = re.compile(r'^\d{7}-\d{4}-\d{7}$')

    def validate(self, value: Any, row_num: int, **kwargs) -> List[ValidationResult]:
        results = []

        if self.is_empty(value):
            results.append(ValidationResult(
                field=self.field_name,
                row=row_num,
                status=ValidationResultStatus.FAIL,
                severity=Severity.ERROR,
                message=f"Field '{self.field_name}' is required but empty",
                original_value=value,
            ))
            return results

        bin_str = str(value).strip()

        # Try to auto-format if needed
        if not self.BIN_PATTERN.match(bin_str):
            results.append(ValidationResult(
                field=self.field_name,
                row=row_num,
                status=ValidationResultStatus.FAIL,
                severity=Severity.ERROR,
                message=f"Invalid BIN format: '{bin_str}'",
                original_value=bin_str,
                suggestion="Format: PSGC(7)-YEAR(4)-INCREMENT(7) e.g., 1400101-2024-0000001",
            ))
        else:
            results.append(ValidationResult(
                field=self.field_name,
                row=row_num,
                status=ValidationResultStatus.PASS,
                severity=Severity.INFO,
                message="Valid BIN",
                original_value=bin_str,
            ))

        return results

    def clean(self, value: Any, **kwargs) -> Tuple[Any, bool]:
        if self.is_empty(value):
            return value, False

        bin_str = str(value).strip()

        # Try to auto-format from various input formats
        # Remove any existing dashes and spaces
        clean_bin = bin_str.replace("-", "").replace(" ", "")

        if len(clean_bin) == 18 and clean_bin.isdigit():
            # Format: 140010120240000001 -> 1400101-2024-0000001
            formatted = f"{clean_bin[0:7]}-{clean_bin[7:11]}-{clean_bin[11:18]}"
            return formatted, formatted != bin_str

        return bin_str, False


class ForeignKeyValidator(BaseValidator):
    """Validates foreign key references exist in parent sheet"""

    def __init__(self, field_name: str = "", parent_sheet: str = "", parent_column: str = ""):
        super().__init__(field_name)
        self.parent_sheet = parent_sheet
        self.parent_column = parent_column
        self.parent_values = set()

    def set_parent_values(self, values: set):
        """Set the valid values from parent sheet"""
        self.parent_values = values

    def validate(self, value: Any, row_num: int, **kwargs) -> List[ValidationResult]:
        results = []

        if self.is_empty(value):
            results.append(ValidationResult(
                field=self.field_name,
                row=row_num,
                status=ValidationResultStatus.FAIL,
                severity=Severity.ERROR,
                message=f"Field '{self.field_name}' is required but empty",
                original_value=value,
            ))
            return results

        str_value = str(value).strip()

        if str_value in self.parent_values:
            results.append(ValidationResult(
                field=self.field_name,
                row=row_num,
                status=ValidationResultStatus.PASS,
                severity=Severity.INFO,
                message=f"Valid reference to {self.parent_sheet}",
                original_value=str_value,
            ))
        else:
            results.append(ValidationResult(
                field=self.field_name,
                row=row_num,
                status=ValidationResultStatus.FAIL,
                severity=Severity.ERROR,
                message=f"Foreign key '{str_value}' not found in {self.parent_sheet}.{self.parent_column}",
                original_value=str_value,
                suggestion=f"Value must exist in {self.parent_sheet}.{self.parent_column}",
            ))

        return results

    def clean(self, value: Any, **kwargs) -> Tuple[Any, bool]:
        # Foreign keys can't be auto-cleaned, must exist in parent
        if self.is_empty(value):
            return value, False
        return str(value).strip(), str(value).strip() != value
