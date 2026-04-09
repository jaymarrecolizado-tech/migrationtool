"""
Sample Plugin: TIN Number Validator
Validates Philippine TIN number format (000-000-000-00000)
"""

import re
from generators.plugin_system import PluginInfo, BasePluginValidator

PLUGIN_INFO = PluginInfo(
    name="TIN Validator",
    version="1.0.0",
    description="Validates Philippine TIN number format",
    plugin_type="validator",
    author="BPLS Team",
)

TIN_PATTERN = re.compile(r"^\d{3}-\d{3}-\d{3}-\d{5}$")


def get_validator():
    return TINValidator()


class TINValidator(BasePluginValidator):
    def validate(self, field_name, value, row, row_num):
        results = []

        # Only validate TIN fields
        if field_name not in ("tin_no", "TIN", "tin"):
            return results

        if value is None or str(value).strip() == "":
            return results  # TIN is optional

        tin_str = str(value).strip()

        if not TIN_PATTERN.match(tin_str):
            results.append({
                "status": "FAIL",
                "severity": "WARNING",
                "field": field_name,
                "row": row_num,
                "message": f"Invalid TIN format: '{tin_str}'. Expected: 000-000-000-00000",
            })

        return results
