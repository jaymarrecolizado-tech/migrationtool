"""
Base Validator and ValidationResult classes
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
from abc import ABC, abstractmethod


class Severity(Enum):
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"


class ValidationResultStatus(Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    AUTO_CORRECTED = "AUTO_CORRECTED"


@dataclass
class ValidationResult:
    """Represents the result of a single validation check"""
    field: str
    row: int
    status: ValidationResultStatus
    severity: Severity
    message: str
    original_value: Any = None
    corrected_value: Any = None
    suggestion: str = ""

    def to_dict(self) -> Dict:
        return {
            "field": self.field,
            "row": self.row,
            "status": self.status.value,
            "severity": self.severity.value,
            "message": self.message,
            "original_value": self.original_value,
            "corrected_value": self.corrected_value,
            "suggestion": self.suggestion,
        }


class BaseValidator(ABC):
    """Abstract base class for all validators"""

    def __init__(self, field_name: str = ""):
        self.field_name = field_name

    @abstractmethod
    def validate(self, value: Any, row_num: int, **kwargs) -> List[ValidationResult]:
        """Validate a value and return results"""
        pass

    @abstractmethod
    def clean(self, value: Any, **kwargs) -> tuple[Any, bool]:
        """
        Clean/normalize a value
        Returns: (cleaned_value, was_modified)
        """
        pass

    def is_empty(self, value: Any) -> bool:
        """Check if value is empty/null"""
        return value is None or (isinstance(value, str) and value.strip() == "")
