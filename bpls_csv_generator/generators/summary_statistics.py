"""
Summary Statistics — Auto-generate counts and analytics from validated data.
"""

from collections import Counter
from dataclasses import dataclass, field


@dataclass
class SheetStatistics:
    sheet: str
    row_count: int
    field_count: int
    numeric_stats: dict[str, dict] = field(default_factory=dict)
    categorical_stats: dict[str, dict] = field(default_factory=dict)
    date_range: dict[str, str] = field(default_factory=dict)


class SummaryStatistics:
    """Generates summary statistics from validated sheet data."""

    def analyze(self, sheet_name: str, rows: list[dict]) -> SheetStatistics:
        """Analyze a sheet and produce statistics."""
        if not rows:
            return SheetStatistics(sheet=sheet_name, row_count=0, field_count=0)

        field_count = len(rows[0])
        numeric_stats = {}
        categorical_stats = {}
        date_fields = set()

        # Detect field types and compute stats
        for key in rows[0].keys():
            values = [row.get(key) for row in rows if row.get(key) is not None and str(row.get(key)).strip() != ""]

            if not values:
                continue

            # Try numeric
            try:
                nums = [float(v) for v in values if v is not None]
                if nums:
                    numeric_stats[key] = {
                        "count": len(nums),
                        "min": min(nums),
                        "max": max(nums),
                        "sum": sum(nums),
                        "mean": sum(nums) / len(nums),
                    }
                    continue
            except (ValueError, TypeError):
                pass

            # Categorical (enum-like)
            unique_vals = set(str(v).strip().lower() for v in values)
            if len(unique_vals) <= 50:  # treat as categorical if low cardinality
                counter = Counter(str(v).strip() for v in values)
                categorical_stats[key] = dict(counter.most_common(20))

        return SheetStatistics(
            sheet=sheet_name,
            row_count=len(rows),
            field_count=field_count,
            numeric_stats=numeric_stats,
            categorical_stats=categorical_stats,
        )

    def generate_business_summary(self, rows: list[dict]) -> dict:
        """Generate a high-level business summary."""
        if not rows:
            return {}

        business_types = Counter()
        municipalities = Counter()
        total_employees = 0
        total_area = 0.0

        for row in rows:
            bt = row.get("business_type", "Unknown")
            business_types[str(bt).strip()] += 1

            muni = row.get("incharge_municipality", "Unknown")
            if muni:
                municipalities[str(muni).strip()] += 1

            try:
                males = int(row.get("no_of_male_employees", 0) or 0)
                females = int(row.get("no_of_female_employees", 0) or 0)
                total_employees += males + females
            except (ValueError, TypeError):
                pass

            try:
                area = float(row.get("area", 0) or 0)
                total_area += area
            except (ValueError, TypeError):
                pass

        return {
            "total_businesses": len(rows),
            "by_type": dict(business_types.most_common()),
            "top_municipalities": dict(municipalities.most_common(10)),
            "total_employees": total_employees,
            "avg_employees_per_business": round(total_employees / len(rows), 1) if rows else 0,
            "total_floor_area_sqm": round(total_area, 2),
        }

    def generate_application_summary(self, rows: list[dict]) -> dict:
        """Generate application-level summary."""
        if not rows:
            return {}

        app_types = Counter()
        payment_modes = Counter()
        total_revenue = 0.0

        for row in rows:
            at = row.get("application_type", "Unknown")
            app_types[str(at).strip()] += 1

            mode = row.get("mode_of_payment", "Unknown")
            payment_modes[str(mode).strip()] += 1

            try:
                total_revenue += float(row.get("total", 0) or 0)
            except (ValueError, TypeError):
                pass

        return {
            "total_applications": len(rows),
            "by_type": dict(app_types.most_common()),
            "by_payment_mode": dict(payment_modes.most_common()),
            "total_revenue": round(total_revenue, 2),
            "avg_revenue_per_application": round(total_revenue / len(rows), 2) if rows else 0,
        }

    def generate_fee_summary(self, rows: list[dict]) -> dict:
        """Generate fee-level summary."""
        if not rows:
            return {}

        fee_types = Counter()
        total_fees = 0.0
        total_discounts = 0.0

        for row in rows:
            ft = row.get("type", "Unknown")
            fee_types[str(ft).strip()] += 1

            try:
                total_fees += float(row.get("amount", 0) or 0)
                total_discounts += float(row.get("discount", 0) or 0)
            except (ValueError, TypeError):
                pass

        return {
            "total_fee_records": len(rows),
            "by_type": dict(fee_types.most_common()),
            "total_fees_assessed": round(total_fees, 2),
            "total_discounts_given": round(total_discounts, 2),
        }

    def generate_full_report(self, sheets_data: dict[str, list[dict]]) -> dict:
        """Generate a comprehensive report across all sheets."""
        report = {}

        for sheet_name, rows in sheets_data.items():
            stats = self.analyze(sheet_name, rows)
            report[sheet_name] = {
                "row_count": stats.row_count,
                "field_count": stats.field_count,
                "numeric_stats": stats.numeric_stats,
                "categorical_stats": stats.categorical_stats,
            }

            # Add domain-specific summaries
            if "Business" in sheet_name and "Activity" not in sheet_name:
                report[sheet_name]["business_summary"] = self.generate_business_summary(rows)
            elif "Application" in sheet_name and "Fee" not in sheet_name:
                report[sheet_name]["application_summary"] = self.generate_application_summary(rows)
            elif "Fee" in sheet_name:
                report[sheet_name]["fee_summary"] = self.generate_fee_summary(rows)

        return report
