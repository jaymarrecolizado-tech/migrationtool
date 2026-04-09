"""
Conditional Validator for BPLS Migration
Handles rules like: "If business_type = SOLE PROPRIETORSHIP, then dti_no is required"
"""

from typing import Any, Dict, List, Optional

from .base import BaseValidator, ValidationResult, ValidationResultStatus, Severity


class ConditionalValidator(BaseValidator):
    """Validates conditional requirements"""

    def __init__(self, field_name: str = ""):
        super().__init__(field_name)

    def validate(
        self,
        value: Any,
        row_num: int,
        condition: Dict,
        required: bool = False,
        validation: str = None,
        alternative_field: str = None,
        row_data: Dict = None,
        **kwargs
    ) -> List[ValidationResult]:
        """
        Validate conditional requirement

        Args:
            value: The field value to validate
            row_num: Row number
            condition: Dict with field and value/value_in/exists to check
            required: Whether field is required when condition is met
            validation: Custom validation expression (e.g., "qtr_to >= qtr_from")
            alternative_field: If this field has value, current field not required
            row_data: Full row data for condition checking
        """
        results = []

        # Check if condition is met
        condition_met = self._check_condition(condition, row_data)

        if not condition_met:
            # Condition not met, skip validation
            return results

        # Condition is met, check if field is required
        if required:
            if self.is_empty(value):
                # Check if alternative field has value
                if alternative_field and row_data and not self.is_empty(row_data.get(alternative_field)):
                    results.append(ValidationResult(
                        field=self.field_name,
                        row=row_num,
                        status=ValidationResultStatus.PASS,
                        severity=Severity.INFO,
                        message=f"Optional (alternative field '{alternative_field}' has value)",
                        original_value=value,
                    ))
                    return results

                results.append(ValidationResult(
                    field=self.field_name,
                    row=row_num,
                    status=ValidationResultStatus.FAIL,
                    severity=Severity.ERROR,
                    message=f"Field '{self.field_name}' is required when {condition['field']} = {condition.get('value', condition.get('value_in'))}",
                    original_value=value,
                    suggestion=f"Provide a value for '{self.field_name}'",
                ))
                return results

        # Custom validation expression
        if validation and row_data:
            try:
                # Evaluate simple expressions like "qtr_to >= qtr_from"
                if ">=" in validation:
                    parts = validation.split(">=")
                    field1 = parts[0].strip()
                    field2 = parts[1].strip()
                    if row_data.get(field1) is not None and row_data.get(field2) is not None:
                        if float(row_data[field1]) < float(row_data[field2]):
                            results.append(ValidationResult(
                                field=self.field_name,
                                row=row_num,
                                status=ValidationResultStatus.FAIL,
                                severity=Severity.ERROR,
                                message=f"{field1} ({row_data[field1]}) must be >= {field2} ({row_data[field2]})",
                                original_value=value,
                            ))
            except Exception as e:
                results.append(ValidationResult(
                    field=self.field_name,
                    row=row_num,
                    status=ValidationResultStatus.FAIL,
                    severity=Severity.WARNING,
                    message=f"Could not evaluate validation expression '{validation}': {str(e)}",
                    original_value=value,
                ))

        if not results:
            results.append(ValidationResult(
                field=self.field_name,
                row=row_num,
                status=ValidationResultStatus.PASS,
                severity=Severity.INFO,
                message="Conditional validation passed",
                original_value=value,
            ))

        return results

    def _check_condition(self, condition: Dict, row_data: Dict) -> bool:
        """Check if a condition is met"""
        if not row_data:
            return False

        field = condition.get("field")
        if not field or field not in row_data:
            return False

        row_value = row_data[field]

        # Check "value" condition (exact match)
        if "value" in condition:
            return self._normalize(row_value) == self._normalize(condition["value"])

        # Check "value_in" condition (value in list)
        if "value_in" in condition:
            normalized_row = self._normalize(row_value)
            normalized_list = [self._normalize(v) for v in condition["value_in"]]
            return normalized_row in normalized_list

        # Check "exists" condition (field has any value)
        if "exists" in condition and condition["exists"]:
            return not self.is_empty(row_value)

        return False

    def _normalize(self, value: Any) -> Any:
        """Normalize value for comparison"""
        if isinstance(value, str):
            return value.strip().upper()
        if isinstance(value, (int, float)):
            return value
        return value

    def clean(self, value: Any, **kwargs) -> tuple:
        # Conditional validation doesn't clean values
        return value, False


class CrossFieldValidator(BaseValidator):
    """Validates relationships between fields in the same row"""

    def __init__(self, field_name: str = "", expression: str = ""):
        super().__init__(field_name)
        self.expression = expression

    def validate(
        self,
        value: Any,
        row_num: int,
        row_data: Dict = None,
        **kwargs
    ) -> List[ValidationResult]:
        results = []

        if not row_data:
            return results

        # Example: total = amount + surcharge + interest - discount
        if "total" in self.field_name.lower():
            try:
                amount = float(row_data.get("amount", 0))
                discount = float(row_data.get("discount", 0))
                surcharge = float(row_data.get("surcharge", 0))
                interest = float(row_data.get("interest", 0))

                expected_total = amount + surcharge + interest - discount
                actual_total = float(value) if not self.is_empty(value) else 0

                if abs(expected_total - actual_total) > 0.01:  # Allow small floating point differences
                    results.append(ValidationResult(
                        field=self.field_name,
                        row=row_num,
                        status=ValidationResultStatus.AUTO_CORRECTED,
                        severity=Severity.INFO,
                        message=f"Auto-calculated: {amount} + {surcharge} + {interest} - {discount} = {expected_total}",
                        original_value=value,
                        corrected_value=expected_total,
                    ))
                else:
                    results.append(ValidationResult(
                        field=self.field_name,
                        row=row_num,
                        status=ValidationResultStatus.PASS,
                        severity=Severity.INFO,
                        message="Total calculation is correct",
                        original_value=value,
                    ))
            except (ValueError, TypeError) as e:
                results.append(ValidationResult(
                    field=self.field_name,
                    row=row_num,
                    status=ValidationResultStatus.FAIL,
                    severity=Severity.ERROR,
                    message=f"Cannot calculate total: {str(e)}",
                    original_value=value,
                ))

        if not results:
            results.append(ValidationResult(
                field=self.field_name,
                row=row_num,
                status=ValidationResultStatus.PASS,
                severity=Severity.INFO,
                message="Cross-field validation passed",
                original_value=value,
            ))

        return results

    def clean(self, value: Any, **kwargs) -> tuple:
        return value, False
