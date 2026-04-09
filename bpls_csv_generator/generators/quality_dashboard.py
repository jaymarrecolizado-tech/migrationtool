"""
Data Quality Dashboard — Score and visualize data quality per sheet.
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class SheetQualityScore:
    sheet: str
    total_rows: int
    total_fields: int
    total_checks: int
    passed_checks: int
    failed_checks: int
    warnings: int
    auto_corrected: int
    quality_score: float  # 0-100
    field_scores: dict[str, float] = field(default_factory=dict)
    category_scores: dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "sheet": self.sheet,
            "total_rows": self.total_rows,
            "total_fields": self.total_fields,
            "total_checks": self.total_checks,
            "passed_checks": self.passed_checks,
            "failed_checks": self.failed_checks,
            "warnings": self.warnings,
            "auto_corrected": self.auto_corrected,
            "quality_score": round(self.quality_score, 1),
            "field_scores": {k: round(v, 1) for k, v in self.field_scores.items()},
            "category_scores": {k: round(v, 1) for k, v in self.category_scores.items()},
        }


class DataQualityDashboard:
    """Calculates data quality scores from validation results."""

    # Category groupings for breakdown
    CATEGORIES = {
        "Identifiers": {"bin", "business_bin", "or_no", "application_or_no", "dti_no", "sec_no", "cda_no", "tin_no"},
        "Names": {"business_name", "trade_name", "lessor_name", "incharge_first_name", "incharge_middle_name", "incharge_last_name", "incharge_extension_name", "code", "description"},
        "Dates": {"dti_registratrion_expiry_date", "application_date", "issued_date", "valid_until", "or_date", "retired_date"},
        "Contact": {"email_address", "cellphone_no", "telephone_no"},
        "Financial": {"amount", "discount", "surcharge", "Interest", "Surcharge", "total", "monthly_rental", "capital_amount", "gross_amount", "gross_amount_essential", "gross_amount_nonessential"},
        "Address": {"office_street", "office_barangay_code", "incharge_street", "incharge_barangay", "incharge_municipality", "incharge_province", "incharge_country_of_citizenship"},
        "Classifications": {"business_type", "application_type", "type", "activity_type", "mode_of_payment", "incharge_sex"},
        "Counts": {"no_of_male_employees", "no_of_female_employees", "no_of_employees_residing_within_the_area", "no_of_van", "no_of_truck", "no_of_motorcycle", "area", "year", "qtr_from", "qtr_to", "business_line_code"},
        "Location": {"location_owned", "tdn_no", "pin_no"},
    }

    def calculate(self, sheet_name: str, rows: list[dict], validation_results: list, transformations: list[dict] | None = None) -> SheetQualityScore:
        """Calculate quality score from validation results."""
        total_rows = len(rows)
        if not rows:
            return SheetQualityScore(sheet=sheet_name, total_rows=0, total_fields=0, total_checks=0, passed_checks=0, failed_checks=0, warnings=0, auto_corrected=0, quality_score=100.0)

        # Determine fields from first row
        all_fields = set(rows[0].keys())
        total_fields = len(all_fields)

        passed = 0
        failed = 0
        warnings = 0
        auto_corrected = 0
        field_results: dict[str, list[str]] = {f: [] for f in all_fields}

        for result in validation_results:
            status = result.get("status", "")
            sev = result.get("severity", "")
            fld = result.get("field", "")

            if fld in field_results:
                field_results[fld].append(status)

            if status == "PASS":
                passed += 1
            elif status == "AUTO_CORRECTED":
                auto_corrected += 1
                passed += 1
            elif status == "FAIL":
                if sev == "WARNING":
                    warnings += 1
                    passed += 1  # warnings don't fail
                else:
                    failed += 1

        total_checks = passed + failed
        quality_score = (passed / total_checks * 100) if total_checks > 0 else 100.0

        # Per-field scores
        field_scores = {}
        for fld, results_list in field_results.items():
            if results_list:
                fld_pass = sum(1 for r in results_list if r in ("PASS", "AUTO_CORRECTED"))
                field_scores[fld] = (fld_pass / len(results_list)) * 100
            else:
                field_scores[fld] = 100.0

        # Category scores
        category_scores = {}
        for cat_name, cat_fields in self.CATEGORIES.items():
            relevant = {f: field_scores.get(f, 100.0) for f in cat_fields if f in field_scores}
            if relevant:
                category_scores[cat_name] = sum(relevant.values()) / len(relevant)

        return SheetQualityScore(
            sheet=sheet_name,
            total_rows=total_rows,
            total_fields=total_fields,
            total_checks=total_checks,
            passed_checks=passed,
            failed_checks=failed,
            warnings=warnings,
            auto_corrected=auto_corrected,
            quality_score=quality_score,
            field_scores=field_scores,
            category_scores=category_scores,
        )

    def grade_label(self, score: float) -> str:
        if score >= 95:
            return "A+"
        elif score >= 90:
            return "A"
        elif score >= 85:
            return "B+"
        elif score >= 80:
            return "B"
        elif score >= 70:
            return "C"
        elif score >= 60:
            return "D"
        else:
            return "F"

    def grade_color(self, score: float) -> str:
        if score >= 90:
            return "#22c55e"  # green
        elif score >= 70:
            return "#f59e0b"  # amber
        else:
            return "#ef4444"  # red
