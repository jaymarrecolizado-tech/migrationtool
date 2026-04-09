"""
Cross-Row Validator — Detect conflicts between rows (same BIN different names, overlapping dates, etc.).
"""

from dataclasses import dataclass


@dataclass
class CrossRowIssue:
    sheet: str
    issue_type: str
    description: str
    row_numbers: list[int]
    field: str
    severity: str = "ERROR"


class CrossRowValidator:
    """Detects conflicts between rows within the same sheet."""

    def validate_all(self, sheet_name: str, rows: list[dict]) -> list[CrossRowIssue]:
        """Run all cross-row validations."""
        issues = []
        validators = {
            "BPLS-Business": self._validate_business,
            "BPLS-Application": self._validate_application,
            "BPLS-Application Fee": self._validate_application_fee,
        }

        validator = validators.get(sheet_name)
        if validator:
            issues.extend(validator(rows))

        return issues

    def _validate_business(self, rows: list[dict]) -> list[CrossRowIssue]:
        """Cross-row checks for BPLS-Business."""
        issues = []

        # 1. Same BIN, different business name
        bin_names: dict[str, dict[str, set[str]]] = {}
        for idx, row in enumerate(rows, 2):
            bin_val = str(row.get("bin", "")).strip().lower()
            name = str(row.get("business_name", "")).strip()
            if not bin_val or not name:
                continue
            if bin_val not in bin_names:
                bin_names[bin_val] = {"names": set(), "rows": []}
            bin_names[bin_val]["names"].add(name)
            bin_names[bin_val]["rows"].append(idx)

        for bin_val, data in bin_names.items():
            if len(data["names"]) > 1:
                issues.append(
                    CrossRowIssue(
                        sheet="BPLS-Business",
                        issue_type="inconsistent_name",
                        description=f"BIN {bin_val} has multiple business names: {', '.join(data['names'])}",
                        row_numbers=data["rows"],
                        field="business_name",
                    )
                )

        # 2. Same business name, different BIN
        name_bins: dict[str, dict] = {}
        for idx, row in enumerate(rows, 2):
            name = str(row.get("business_name", "")).strip().lower()
            bin_val = str(row.get("bin", "")).strip()
            if not name or not bin_val:
                continue
            if name not in name_bins:
                name_bins[name] = {"bins": set(), "rows": [], "display_name": str(row.get("business_name", ""))}
            name_bins[name]["bins"].add(bin_val)
            name_bins[name]["rows"].append(idx)

        for name, data in name_bins.items():
            if len(data["bins"]) > 1:
                issues.append(
                    CrossRowIssue(
                        sheet="BPLS-Business",
                        issue_type="duplicate_business_name",
                        description=f"Business name '{data['display_name']}' has multiple BINs: {', '.join(data['bins'])}",
                        row_numbers=data["rows"],
                        field="bin",
                        severity="WARNING",
                    )
                )

        return issues

    def _validate_application(self, rows: list[dict]) -> list[CrossRowIssue]:
        """Cross-row checks for BPLS-Application."""
        issues = []

        # 1. Duplicate OR numbers
        or_rows: dict[str, list[int]] = {}
        for idx, row in enumerate(rows, 2):
            or_no = str(row.get("or_no", "")).strip().lower()
            if not or_no:
                continue
            if or_no not in or_rows:
                or_rows[or_no] = []
            or_rows[or_no].append(idx)

        for or_no, row_nums in or_rows.items():
            if len(row_nums) > 1:
                issues.append(
                    CrossRowIssue(
                        sheet="BPLS-Application",
                        issue_type="duplicate_or_number",
                        description=f"Duplicate OR number: {or_no}",
                        row_numbers=row_nums,
                        field="or_no",
                    )
                )

        # 2. Same BIN, same application type, same year (potential double application)
        app_keys: dict[str, list[int]] = {}
        for idx, row in enumerate(rows, 2):
            bin_val = str(row.get("business_bin", "")).strip().lower()
            app_type = str(row.get("application_type", "")).strip()
            year = str(row.get("year", "")).strip()
            key = f"{bin_val}|{app_type}|{year}"
            if key not in app_keys:
                app_keys[key] = []
            app_keys[key].append(idx)

        for key, row_nums in app_keys.items():
            if len(row_nums) > 1:
                parts = key.split("|")
                issues.append(
                    CrossRowIssue(
                        sheet="BPLS-Application",
                        issue_type="potential_double_application",
                        description=f"Same BIN ({parts[0]}), type ({parts[1]}), year ({parts[2]}) — potential duplicate",
                        row_numbers=row_nums,
                        field="business_bin",
                        severity="WARNING",
                    )
                )

        return issues

    def _validate_application_fee(self, rows: list[dict]) -> list[CrossRowIssue]:
        """Cross-row checks for BPLS-Application Fee."""
        issues = []

        # 1. Same OR number, same fee code, same year (duplicate fee entry)
        fee_keys: dict[str, list[int]] = {}
        for idx, row in enumerate(rows, 2):
            or_no = str(row.get("application_or_no", "")).strip().lower()
            code = str(row.get("code", "")).strip().lower()
            year = str(row.get("year", "")).strip()
            key = f"{or_no}|{code}|{year}"
            if key not in fee_keys:
                fee_keys[key] = []
            fee_keys[key].append(idx)

        for key, row_nums in fee_keys.items():
            if len(row_nums) > 1:
                parts = key.split("|")
                issues.append(
                    CrossRowIssue(
                        sheet="BPLS-Application Fee",
                        issue_type="duplicate_fee_entry",
                        description=f"Same OR ({parts[0]}), fee code ({parts[1]}), year ({parts[2]}) — potential duplicate",
                        row_numbers=row_nums,
                        field="code",
                        severity="WARNING",
                    )
                )

        return issues
