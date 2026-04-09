"""
Column Mapper — Map source file columns to target BPLS schema fields.
"""

import re
from difflib import SequenceMatcher


class ColumnMapper:
    """Maps arbitrary source column names to BPLS schema field names."""

    # Manual alias registry for common variations
    ALIASES = {
        # BPLS-Business
        "business identification number": "bin",
        "business id": "bin",
        "bin number": "bin",
        "business name": "business_name",
        "biz name": "business_name",
        "company name": "business_name",
        "trade name": "trade_name",
        "doing business as": "trade_name",
        "dba": "trade_name",
        "business type": "business_type",
        "ownership type": "business_type",
        "entity type": "business_type",
        "dti": "dti_no",
        "dti number": "dti_no",
        "dti reg": "dti_no",
        "dti expiry": "dti_registratrion_expiry_date",
        "dti expiration": "dti_registratrion_expiry_date",
        "sec": "sec_no",
        "sec number": "sec_no",
        "sec reg": "sec_no",
        "cda": "cda_no",
        "cda number": "cda_no",
        "tin": "tin_no",
        "tax id": "tin_no",
        "tin number": "tin_no",
        "email": "email_address",
        "email addr": "email_address",
        "contact email": "email_address",
        "phone": "cellphone_no",
        "cellphone": "cellphone_no",
        "mobile": "cellphone_no",
        "cell": "cellphone_no",
        "contact number": "cellphone_no",
        "telephone": "telephone_no",
        "landline": "telephone_no",
        "tel no": "telephone_no",
        "person in charge": "incharge_first_name",
        "incharge": "incharge_first_name",
        "contact person": "incharge_first_name",
        "incharge first name": "incharge_first_name",
        "incharge middle name": "incharge_middle_name",
        "incharge last name": "incharge_last_name",
        "incharge suffix": "incharge_extension_name",
        "incharge extension": "incharge_extension_name",
        "incharge sex": "incharge_sex",
        "incharge gender": "incharge_sex",
        "sex": "incharge_sex",
        "gender": "incharge_sex",
        "incharge citizenship": "incharge_country_of_citizenship",
        "incharge street": "incharge_street",
        "incharge barangay": "incharge_barangay",
        "incharge municipality": "incharge_municipality",
        "incharge province": "incharge_province",
        "office street": "office_street",
        "office address": "office_street",
        "business street": "office_street",
        "office barangay": "office_barangay_code",
        "office brgy code": "office_barangay_code",
        "barangay code": "office_barangay_code",
        "location owned": "location_owned",
        "owned": "location_owned",
        "is owned": "location_owned",
        "tdn": "tdn_no",
        "tax dec number": "tdn_no",
        "tax declaration": "tdn_no",
        "pin": "pin_no",
        "property id": "pin_no",
        "property identification": "pin_no",
        "lessor": "lessor_name",
        "lessor name": "lessor_name",
        "owner name": "lessor_name",
        "monthly rental": "monthly_rental",
        "rent": "monthly_rental",
        "monthly rent": "monthly_rental",
        "floor area": "area",
        "total area": "area",
        "area sqm": "area",
        "male employees": "no_of_male_employees",
        "no male": "no_of_male_employees",
        "female employees": "no_of_female_employees",
        "no female": "no_of_female_employees",
        "employees residing": "no_of_employees_residing_within_the_area",
        "local employees": "no_of_employees_residing_within_the_area",
        "no of van": "no_of_van",
        "vans": "no_of_van",
        "no of truck": "no_of_truck",
        "trucks": "no_of_truck",
        "no of motorcycle": "no_of_motorcycle",
        "motorcycles": "no_of_motorcycle",
        "activity type": "activity_type",
        "office type": "activity_type",
        # BPLS-Application
        "business bin": "business_bin",
        "application type": "application_type",
        "app type": "application_type",
        "application date": "application_date",
        "app date": "application_date",
        "transaction date": "application_date",
        "year": "year",
        "qtr from": "qtr_from",
        "quarter from": "qtr_from",
        "qtr to": "qtr_to",
        "quarter to": "qtr_to",
        "amount": "amount",
        "fee amount": "amount",
        "discount": "discount",
        "surcharge": "surcharge",
        "penalty": "surcharge",
        "interest": "interest",
        "total": "total",
        "total amount": "total",
        "issued date": "issued_date",
        "issue date": "issued_date",
        "valid until": "valid_until",
        "expiry date": "valid_until",
        "or number": "or_no",
        "or no": "or_no",
        "receipt number": "or_no",
        "or date": "or_date",
        "receipt date": "or_date",
        "permit number": "permit_no",
        "permit no": "permit_no",
        "barangay clearance": "barangay_clearance_number",
        "plate number": "business_plate_number",
        "mode of payment": "mode_of_payment",
        "payment mode": "mode_of_payment",
        # BPLS-Application Fee
        "application or no": "application_or_no",
        "fee code": "code",
        "code": "code",
        "description": "description",
        "fee description": "description",
        "fee type": "type",
        "fee year": "year",
    }

    def __init__(self, threshold: float = 0.6):
        self.threshold = threshold

    def map_columns(
        self, source_columns: list[str], target_sheet: str
    ) -> dict[str, str]:
        """
        Map source column names to target BPLS schema fields.
        Returns: {source_column: target_field}
        """
        from config.schema import SHEET_SCHEMAS

        if target_sheet not in SHEET_SCHEMAS:
            raise ValueError(f"Unknown sheet: {target_sheet}")

        target_fields = list(SHEET_SCHEMAS[target_sheet].keys())
        mapping = {}

        for src_col in source_columns:
            best_match = None
            best_score = 0.0

            # 1. Check exact match (case-insensitive)
            normalized_src = self._normalize(src_col)
            for tgt_field in target_fields:
                normalized_tgt = self._normalize(tgt_field)
                if normalized_src == normalized_tgt:
                    best_match = tgt_field
                    best_score = 1.0
                    break

            # 2. Check aliases
            if best_score < 1.0:
                alias_match = self.ALIASES.get(normalized_src)
                if alias_match and alias_match in target_fields:
                    best_match = alias_match
                    best_score = 0.95

            # 3. Fuzzy match
            if best_score < self.threshold:
                for tgt_field in target_fields:
                    score = SequenceMatcher(
                        None, normalized_src, self._normalize(tgt_field)
                    ).ratio()
                    if score > best_score:
                        best_score = score
                        best_match = tgt_field

            if best_match and best_score >= self.threshold:
                mapping[src_col] = best_match

        return mapping

    def auto_detect_sheet(self, source_columns: list[str]) -> list[tuple[str, float]]:
        """
        Auto-detect which BPLS sheet the source columns belong to.
        Returns list of (sheet_name, confidence_score) sorted by score.
        """
        from config.schema import SHEET_SCHEMAS

        scores = []
        for sheet_name, schema in SHEET_SCHEMAS.items():
            target_fields = set(schema.keys())
            mapped = self.map_columns(source_columns, sheet_name)
            matched = len(mapped)
            total_required = len(target_fields)
            confidence = matched / total_required if total_required > 0 else 0
            scores.append((sheet_name, round(confidence, 2)))

        return sorted(scores, key=lambda x: x[1], reverse=True)

    def generate_mapping_report(
        self, source_columns: list[str], target_sheet: str
    ) -> dict:
        """Generate a detailed mapping report."""
        mapping = self.map_columns(source_columns, target_sheet)
        mapped_set = set(mapping.values())
        from config.schema import SHEET_SCHEMAS

        all_fields = set(SHEET_SCHEMAS[target_sheet].keys())
        unmapped = all_fields - mapped_set

        return {
            "target_sheet": target_sheet,
            "source_columns": source_columns,
            "mapped": mapping,
            "unmapped_fields": sorted(unmapped),
            "coverage": f"{len(mapped)}/{len(all_fields)}",
        }

    @staticmethod
    def _normalize(s: str) -> str:
        return re.sub(r"[\s_\-]+", " ", s.strip().lower())
