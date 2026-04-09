"""
Cross-Sheet Validator for BPLS Migration
Validates foreign key relationships between sheets
"""

from typing import Dict, List, Set, Tuple
from validators.base import ValidationResult, ValidationResultStatus, Severity


class CrossSheetValidator:
    """Validates foreign key references across sheets"""

    def __init__(self):
        self.sheet_data: Dict[str, List[Dict]] = {}
        self.validation_results: List[ValidationResult] = []

    def load_sheet_data(self, sheet_name: str, data: List[Dict]):
        """Load sheet data for validation"""
        self.sheet_data[sheet_name] = data

    def validate_all(self) -> List[ValidationResult]:
        """Run all cross-sheet validations"""
        self.validation_results = []

        # Validate BPLS-Business Activity -> BPLS-Business
        if "BPLS-Business Activity" in self.sheet_data and "BPLS-Business" in self.sheet_data:
            self._validate_foreign_key(
                child_sheet="BPLS-Business Activity",
                child_column="bin",
                parent_sheet="BPLS-Business",
                parent_column="bin",
            )

        # Validate BPLS-Application -> BPLS-Business
        if "BPLS-Application" in self.sheet_data and "BPLS-Business" in self.sheet_data:
            self._validate_foreign_key(
                child_sheet="BPLS-Application",
                child_column="business_bin",
                parent_sheet="BPLS-Business",
                parent_column="bin",
            )

        # Validate BPLS-Application Fee -> BPLS-Business
        if "BPLS-Application Fee" in self.sheet_data and "BPLS-Business" in self.sheet_data:
            self._validate_foreign_key(
                child_sheet="BPLS-Application Fee",
                child_column="business_bin",
                parent_sheet="BPLS-Business",
                parent_column="bin",
            )

        # Validate BPLS-Application Fee -> BPLS-Application (application_or_no -> or_no)
        if "BPLS-Application Fee" in self.sheet_data and "BPLS-Application" in self.sheet_data:
            self._validate_foreign_key(
                child_sheet="BPLS-Application Fee",
                child_column="application_or_no",
                parent_sheet="BPLS-Application",
                parent_column="or_no",
            )

        return self.validation_results

    def _validate_foreign_key(
        self,
        child_sheet: str,
        child_column: str,
        parent_sheet: str,
        parent_column: str,
    ):
        """Validate foreign key references"""

        # Get parent values
        parent_values: Set[str] = set()
        for row in self.sheet_data.get(parent_sheet, []):
            if parent_column in row and row[parent_column] is not None:
                parent_values.add(str(row[parent_column]).strip())

        # Validate child references
        for row_idx, row in enumerate(self.sheet_data.get(child_sheet, []), start=2):
            if child_column not in row:
                continue

            child_value = row[child_column]
            if child_value is None or (isinstance(child_value, str) and child_value.strip() == ""):
                continue

            str_value = str(child_value).strip()

            if str_value not in parent_values:
                self.validation_results.append(ValidationResult(
                    field=child_column,
                    row=row_idx,
                    status=ValidationResultStatus.FAIL,
                    severity=Severity.ERROR,
                    message=f"Reference '{str_value}' not found in {parent_sheet}.{parent_column}",
                    original_value=str_value,
                    suggestion=f"Value must exist in {parent_sheet}.{parent_column}",
                ))

    def get_orphaned_records(self) -> Dict[str, List[Dict]]:
        """Get records that have invalid foreign key references"""
        orphaned = {}

        for result in self.validation_results:
            if result.status == ValidationResultStatus.FAIL:
                sheet_name = result.field  # This is simplified, needs enhancement
                if sheet_name not in orphaned:
                    orphaned[sheet_name] = []
                orphaned[sheet_name].append(result.to_dict())

        return orphaned

    def get_summary(self) -> Dict:
        """Get summary of cross-sheet validation"""
        return {
            "total_issues": len(self.validation_results),
            "errors": sum(1 for r in self.validation_results if r.severity == Severity.ERROR),
            "warnings": sum(1 for r in self.validation_results if r.severity == Severity.WARNING),
            "by_sheet": self._group_by_sheet(),
        }

    def _group_by_sheet(self) -> Dict[str, int]:
        """Group issues by sheet"""
        counts = {}
        for result in self.validation_results:
            # Simplified - in real implementation, track sheet name
            counts["unknown"] = counts.get("unknown", 0) + 1
        return counts
