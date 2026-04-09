"""
BPLS Migration Schema Definition — STRICTLY based on "migration rules.xlsx"
as of 29 September 2025
"""

from enum import Enum
from typing import Any, Dict, List, Optional


class FieldType(Enum):
    STRING = "string"
    NUMBER = "number"
    INTEGER = "integer"
    DATE = "date"
    ENUM = "enum"
    BOOLEAN = "boolean"
    EMAIL = "email"
    PHONE = "phone"
    FOREIGN_KEY = "foreign_key"
    BIN = "bin"


class RequiredLevel(Enum):
    YES = "YES"
    NO = "NO"
    CONDITIONAL = "CONDITIONAL"


class FieldDefinition:
    def __init__(
        self,
        name: str,
        field_type: FieldType,
        required: RequiredLevel,
        description: str = "",
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None,
        enum_values: Optional[List[str]] = None,
        format_pattern: Optional[str] = None,
        foreign_key_sheet: Optional[str] = None,
        foreign_key_column: Optional[str] = None,
        default_value: Optional[Any] = None,
        auto_calculate: Optional[str] = None,
    ):
        self.name = name
        self.field_type = field_type
        self.required = required
        self.description = description
        self.min_length = min_length
        self.max_length = max_length
        self.min_value = min_value
        self.max_value = max_value
        self.enum_values = enum_values or []
        self.format_pattern = format_pattern
        self.foreign_key_sheet = foreign_key_sheet
        self.foreign_key_column = foreign_key_column
        self.default_value = default_value
        self.auto_calculate = auto_calculate


# ============================================================
# BPLS-Business Sheet Schema
# Rules from Excel "migration rules.xlsx" sheet "BPLS-Business"
# ============================================================
BPLS_BUSINESS_SCHEMA: Dict[str, FieldDefinition] = {
    "bin": FieldDefinition(
        name="bin",
        field_type=FieldType.BIN,
        required=RequiredLevel.YES,
        description="Business identification number. Format: PSGC(7digits)-YEAR(4digits)-INCREMENT(7digits). Numbers only.",
        format_pattern=r"^\d{7}-\d{4}-\d{7}$",
    ),
    "business_name": FieldDefinition(
        name="business_name",
        field_type=FieldType.STRING,
        required=RequiredLevel.YES,
        description="Registered business name. At least 3 characters.",
        min_length=3,
        max_length=100,
    ),
    "trade_name": FieldDefinition(
        name="trade_name",
        field_type=FieldType.STRING,
        required=RequiredLevel.NO,
        description="Trade name if different from registered name. At least 3 characters.",
        min_length=3,
        max_length=100,
    ),
    "business_type": FieldDefinition(
        name="business_type",
        field_type=FieldType.ENUM,
        required=RequiredLevel.YES,
        description="Business ownership type. Must be all caps.",
        enum_values=[
            "SOLE PROPRIETORSHIP",
            "ONE PERSON CORPORATION",
            "PARTNERSHIP",
            "CORPORATION",
            "COOPERATIVE",
        ],
    ),
    "dti_no": FieldDefinition(
        name="dti_no",
        field_type=FieldType.STRING,
        required=RequiredLevel.CONDITIONAL,
        description="DTI Registration Number. Required when business_type = SOLE PROPRIETORSHIP.",
        min_length=3,
        max_length=30,
    ),
    "dti_registratrion_expiry_date": FieldDefinition(
        name="dti_registratrion_expiry_date",
        field_type=FieldType.DATE,
        required=RequiredLevel.CONDITIONAL,
        description="DTI Registration Expiry Date. Required when business_type = SOLE PROPRIETORSHIP. Format: MM/DD/YYYY",
    ),
    "sec_no": FieldDefinition(
        name="sec_no",
        field_type=FieldType.STRING,
        required=RequiredLevel.CONDITIONAL,
        description="SEC Registration Number. Required when business_type = ONE PERSON CORPORATION, PARTNERSHIP, or CORPORATION.",
        min_length=3,
        max_length=30,
    ),
    "cda_no": FieldDefinition(
        name="cda_no",
        field_type=FieldType.STRING,
        required=RequiredLevel.CONDITIONAL,
        description="CDA Registration Number. Required when business_type = COOPERATIVE.",
        min_length=3,
        max_length=30,
    ),
    "tin_no": FieldDefinition(
        name="tin_no",
        field_type=FieldType.STRING,
        required=RequiredLevel.NO,
        description="TIN Number. Format: 000-000-000-00000",
        min_length=3,
        max_length=20,
    ),
    "email_address": FieldDefinition(
        name="email_address",
        field_type=FieldType.EMAIL,
        required=RequiredLevel.YES,
        description="Active email address. 3-100 characters.",
        min_length=3,
        max_length=100,
    ),
    "cellphone_no": FieldDefinition(
        name="cellphone_no",
        field_type=FieldType.PHONE,
        required=RequiredLevel.YES,
        description="Active cellphone/mobile number. Must start with '639'. 639 + 9 digits = 12 chars.",
        min_length=12,
        max_length=12,
    ),
    "telephone_no": FieldDefinition(
        name="telephone_no",
        field_type=FieldType.STRING,
        required=RequiredLevel.NO,
        description="Active telephone number. 3-20 characters.",
        min_length=3,
        max_length=20,
    ),
    "incharge_first_name": FieldDefinition(
        name="incharge_first_name",
        field_type=FieldType.STRING,
        required=RequiredLevel.YES,
        description="First name of person-in-charge.",
        min_length=3,
        max_length=100,
    ),
    "incharge_middle_name": FieldDefinition(
        name="incharge_middle_name",
        field_type=FieldType.STRING,
        required=RequiredLevel.NO,
        description="Middle name of person-in-charge.",
        min_length=3,
        max_length=100,
    ),
    "incharge_last_name": FieldDefinition(
        name="incharge_last_name",
        field_type=FieldType.STRING,
        required=RequiredLevel.YES,
        description="Last name of person-in-charge.",
        min_length=3,
        max_length=100,
    ),
    "incharge_extension_name": FieldDefinition(
        name="incharge_extension_name",
        field_type=FieldType.STRING,
        required=RequiredLevel.NO,
        description="Extension name. Do not include period (.).",
        min_length=3,
        max_length=100,
    ),
    "incharge_sex": FieldDefinition(
        name="incharge_sex",
        field_type=FieldType.ENUM,
        required=RequiredLevel.YES,
        description="Sex of person-in-charge.",
        enum_values=["M", "F"],
    ),
    "incharge_country_of_citizenship": FieldDefinition(
        name="incharge_country_of_citizenship",
        field_type=FieldType.STRING,
        required=RequiredLevel.YES,
        description="Country of Citizenship of person-in-charge.",
        min_length=3,
        max_length=100,
    ),
    "incharge_street": FieldDefinition(
        name="incharge_street",
        field_type=FieldType.STRING,
        required=RequiredLevel.NO,
        description="Street address of person-in-charge.",
        min_length=3,
        max_length=100,
    ),
    "incharge_barangay": FieldDefinition(
        name="incharge_barangay",
        field_type=FieldType.STRING,
        required=RequiredLevel.YES,
        description="Barangay address of person-in-charge.",
        min_length=3,
        max_length=100,
    ),
    "incharge_municipality": FieldDefinition(
        name="incharge_municipality",
        field_type=FieldType.STRING,
        required=RequiredLevel.YES,
        description="City/Municipality address of person-in-charge.",
        min_length=3,
        max_length=100,
    ),
    "incharge_province": FieldDefinition(
        name="incharge_province",
        field_type=FieldType.STRING,
        required=RequiredLevel.YES,
        description="Provincial address of person-in-charge.",
        min_length=3,
        max_length=100,
    ),
    "office_street": FieldDefinition(
        name="office_street",
        field_type=FieldType.STRING,
        required=RequiredLevel.NO,
        description="Street address of the business.",
        min_length=3,
        max_length=100,
    ),
    "office_barangay_code": FieldDefinition(
        name="office_barangay_code",
        field_type=FieldType.INTEGER,
        required=RequiredLevel.YES,
        description="Geocode of barangay address of the business.",
    ),
    "location_owned": FieldDefinition(
        name="location_owned",
        field_type=FieldType.BOOLEAN,
        required=RequiredLevel.YES,
        description="Whether location is owned (1) or rented (0). Accepted: 1, 0, true, false.",
    ),
    "tdn_no": FieldDefinition(
        name="tdn_no",
        field_type=FieldType.STRING,
        required=RequiredLevel.CONDITIONAL,
        description="Tax Declaration Number. Required when location_owned = 1 and pin_no is null. 3-20 chars.",
        min_length=3,
        max_length=20,
    ),
    "pin_no": FieldDefinition(
        name="pin_no",
        field_type=FieldType.STRING,
        required=RequiredLevel.CONDITIONAL,
        description="Property Identification Number. Required when location_owned = 1 and tdn_no is null. Numbers only 3-20.",
        min_length=3,
        max_length=20,
    ),
    "lessor_name": FieldDefinition(
        name="lessor_name",
        field_type=FieldType.STRING,
        required=RequiredLevel.CONDITIONAL,
        description="Full name of lessor. Required when location_owned = 0. 3-150 chars.",
        min_length=3,
        max_length=150,
    ),
    "monthly_rental": FieldDefinition(
        name="monthly_rental",
        field_type=FieldType.NUMBER,
        required=RequiredLevel.CONDITIONAL,
        description="Monthly rental amount. Required when location_owned = 0.",
        min_value=0,
    ),
    "area": FieldDefinition(
        name="area",
        field_type=FieldType.NUMBER,
        required=RequiredLevel.YES,
        description="Total floor area of the business.",
        min_value=0,
    ),
    "no_of_male_employees": FieldDefinition(
        name="no_of_male_employees",
        field_type=FieldType.INTEGER,
        required=RequiredLevel.YES,
        description="Total number of male employees.",
        min_value=0,
    ),
    "no_of_female_employees": FieldDefinition(
        name="no_of_female_employees",
        field_type=FieldType.INTEGER,
        required=RequiredLevel.YES,
        description="Total number of female employees.",
        min_value=0,
    ),
    "no_of_employees_residing_within_the_area": FieldDefinition(
        name="no_of_employees_residing_within_the_area",
        field_type=FieldType.INTEGER,
        required=RequiredLevel.YES,
        description="Total employees within the LGU. Must be <= (no_of_male_employees + no_of_female_employees).",
        min_value=0,
    ),
    "no_of_van": FieldDefinition(
        name="no_of_van",
        field_type=FieldType.INTEGER,
        required=RequiredLevel.YES,
        description="Total number of vans.",
        min_value=0,
    ),
    "no_of_truck": FieldDefinition(
        name="no_of_truck",
        field_type=FieldType.INTEGER,
        required=RequiredLevel.YES,
        description="Total number of trucks.",
        min_value=0,
    ),
    "no_of_motorcycle": FieldDefinition(
        name="no_of_motorcycle",
        field_type=FieldType.INTEGER,
        required=RequiredLevel.YES,
        description="Total number of motorcycles.",
        min_value=0,
    ),
    "activity_type": FieldDefinition(
        name="activity_type",
        field_type=FieldType.ENUM,
        required=RequiredLevel.YES,
        description="Primary function of business location.",
        enum_values=[
            "Main Office",
            "Branch Office",
            "Admin Office Only",
            "Warehouse",
            "Others",
        ],
    ),
}

# ============================================================
# BPLS-Business Activity Sheet Schema
# Rules from Excel "migration rules.xlsx" sheet "BPLS-Business Activity"
# ============================================================
BPLS_BUSINESS_ACTIVITY_SCHEMA: Dict[str, FieldDefinition] = {
    "bin": FieldDefinition(
        name="bin",
        field_type=FieldType.BIN,
        required=RequiredLevel.YES,
        description="Business identification number. Must exist in BPLS-Business sheet.",
        format_pattern=r"^\d{7}-\d{4}-\d{7}$",
        foreign_key_sheet="BPLS-Business",
        foreign_key_column="bin",
    ),
    "business_line_code": FieldDefinition(
        name="business_line_code",
        field_type=FieldType.INTEGER,
        required=RequiredLevel.YES,
        description="Code of business line. Must exist in business line in Core.",
    ),
    "capital_amount": FieldDefinition(
        name="capital_amount",
        field_type=FieldType.NUMBER,
        required=RequiredLevel.YES,
        description="Capital amount during new registration. Input 0 if not applicable.",
        min_value=0,
    ),
    "gross_amount": FieldDefinition(
        name="gross_amount",
        field_type=FieldType.NUMBER,
        required=RequiredLevel.YES,
        description="Total gross amount. Input 0 if not applicable.",
        min_value=0,
    ),
    "gross_amount_essential": FieldDefinition(
        name="gross_amount_essential",
        field_type=FieldType.NUMBER,
        required=RequiredLevel.YES,
        description="Essential gross amount. Input 0 if not applicable.",
        min_value=0,
    ),
    "gross_amount_nonessential": FieldDefinition(
        name="gross_amount_nonessential",
        field_type=FieldType.NUMBER,
        required=RequiredLevel.YES,
        description="Non-essential gross amount. Input 0 if not applicable.",
        min_value=0,
    ),
    "retired_date": FieldDefinition(
        name="retired_date",
        field_type=FieldType.DATE,
        required=RequiredLevel.NO,
        description="Retired date. Format MM/DD/YYYY. Leave blank if not applicable.",
    ),
}

# ============================================================
# BPLS-Application Sheet Schema
# Rules from Excel "migration rules.xlsx" sheet "BPLS-Application"
# ============================================================
BPLS_APPLICATION_SCHEMA: Dict[str, FieldDefinition] = {
    "business_bin": FieldDefinition(
        name="business_bin",
        field_type=FieldType.BIN,
        required=RequiredLevel.YES,
        description="Business identification number. Must exist in BPLS-Business sheet.",
        format_pattern=r"^\d{7}-\d{4}-\d{7}$",
        foreign_key_sheet="BPLS-Business",
        foreign_key_column="bin",
    ),
    "application_type": FieldDefinition(
        name="application_type",
        field_type=FieldType.ENUM,
        required=RequiredLevel.YES,
        description="Application type: N=NEW, R=RENEWAL, Q=QUARTERLY.",
        enum_values=["N", "R", "Q"],
    ),
    "application_date": FieldDefinition(
        name="application_date",
        field_type=FieldType.DATE,
        required=RequiredLevel.YES,
        description="Transaction date of application. Format: mm/dd/yyyy.",
    ),
    "year": FieldDefinition(
        name="year",
        field_type=FieldType.INTEGER,
        required=RequiredLevel.YES,
        description="Transaction year of the application.",
        min_value=2000,
        max_value=2100,
    ),
    "qtr_from": FieldDefinition(
        name="qtr_from",
        field_type=FieldType.INTEGER,
        required=RequiredLevel.NO,
        description="Starting quarter. Accepted values: 1,2,3,4.",
        min_value=1,
        max_value=4,
    ),
    "qtr_to": FieldDefinition(
        name="qtr_to",
        field_type=FieldType.INTEGER,
        required=RequiredLevel.NO,
        description="Ending quarter. Must be >= qtr_from. Accepted values: 1,2,3,4.",
        min_value=1,
        max_value=4,
    ),
    "amount": FieldDefinition(
        name="amount",
        field_type=FieldType.NUMBER,
        required=RequiredLevel.YES,
        description="Computed amount of the application.",
        min_value=0,
    ),
    "discount": FieldDefinition(
        name="discount",
        field_type=FieldType.NUMBER,
        required=RequiredLevel.YES,
        description="Discount amount.",
        min_value=0,
    ),
    "surcharge": FieldDefinition(
        name="surcharge",
        field_type=FieldType.NUMBER,
        required=RequiredLevel.YES,
        description="Penalty/surcharge amount.",
        min_value=0,
    ),
    "interest": FieldDefinition(
        name="interest",
        field_type=FieldType.NUMBER,
        required=RequiredLevel.YES,
        description="Penalty/interest amount.",
        min_value=0,
    ),
    "total": FieldDefinition(
        name="total",
        field_type=FieldType.NUMBER,
        required=RequiredLevel.YES,
        description="Total = amount + surcharge + interest - discount.",
        min_value=0,
        auto_calculate="amount + surcharge + interest - discount",
    ),
    "issued_date": FieldDefinition(
        name="issued_date",
        field_type=FieldType.DATE,
        required=RequiredLevel.YES,
        description="Transaction issued date. Format: mm/dd/yyyy.",
    ),
    "valid_until": FieldDefinition(
        name="valid_until",
        field_type=FieldType.DATE,
        required=RequiredLevel.YES,
        description="Transaction validity date. Format: mm/dd/yyyy.",
    ),
    "or_no": FieldDefinition(
        name="or_no",
        field_type=FieldType.STRING,
        required=RequiredLevel.YES,
        description="Official receipt number. Must be unique in permit applications. Alphanumeric.",
        min_length=1,
        max_length=50,
    ),
    "or_date": FieldDefinition(
        name="or_date",
        field_type=FieldType.DATE,
        required=RequiredLevel.YES,
        description="Transaction OR date. Format: mm/dd/yyyy.",
    ),
    "permit_no": FieldDefinition(
        name="permit_no",
        field_type=FieldType.STRING,
        required=RequiredLevel.NO,
        description="Permit number issued to the business. Alphanumeric.",
        min_length=1,
        max_length=50,
    ),
    "barangay_clearance_number": FieldDefinition(
        name="barangay_clearance_number",
        field_type=FieldType.STRING,
        required=RequiredLevel.NO,
        description="Barangay Business Clearance number. Alphanumeric.",
        min_length=1,
        max_length=50,
    ),
    "business_plate_number": FieldDefinition(
        name="business_plate_number",
        field_type=FieldType.STRING,
        required=RequiredLevel.NO,
        description="Business permit plate number. Alphanumeric.",
        min_length=1,
        max_length=50,
    ),
    "mode_of_payment": FieldDefinition(
        name="mode_of_payment",
        field_type=FieldType.STRING,
        required=RequiredLevel.YES,
        description="Mode of payment: ONLINE or MANUAL. Alphanumeric.",
        min_length=2,
        max_length=20,
    ),
}

# ============================================================
# BPLS-Application Fee Sheet Schema
# Rules from Excel "migration rules.xlsx" sheet "BPLS-Application Fee"
# ============================================================
BPLS_APPLICATION_FEE_SCHEMA: Dict[str, FieldDefinition] = {
    "business_bin": FieldDefinition(
        name="business_bin",
        field_type=FieldType.BIN,
        required=RequiredLevel.YES,
        description="Business identification number. Format: PSGC(7)-YEAR(4)-INCREMENT(7). Must exist in businesses.",
        format_pattern=r"^\d{7}-\d{4}-\d{7}$",
        foreign_key_sheet="BPLS-Business",
        foreign_key_column="bin",
    ),
    "application_or_no": FieldDefinition(
        name="application_or_no",
        field_type=FieldType.STRING,
        required=RequiredLevel.YES,
        description="Transaction/OR number. Must exist in permit applications.",
        min_length=1,
        max_length=50,
        foreign_key_sheet="BPLS-Application",
        foreign_key_column="or_no",
    ),
    "code": FieldDefinition(
        name="code",
        field_type=FieldType.STRING,
        required=RequiredLevel.YES,
        description="Unique fee code. Alphanumeric, min 2, max 20.",
        min_length=2,
        max_length=20,
    ),
    "description": FieldDefinition(
        name="description",
        field_type=FieldType.STRING,
        required=RequiredLevel.YES,
        description="Fee label/name. Min 2, max 100 chars.",
        min_length=2,
        max_length=100,
    ),
    "amount": FieldDefinition(
        name="amount",
        field_type=FieldType.NUMBER,
        required=RequiredLevel.YES,
        description="Computed amount.",
        min_value=0,
    ),
    "discount": FieldDefinition(
        name="discount",
        field_type=FieldType.NUMBER,
        required=RequiredLevel.YES,
        description="Discount amount.",
        min_value=0,
    ),
    "Interest": FieldDefinition(
        name="Interest",
        field_type=FieldType.NUMBER,
        required=RequiredLevel.YES,
        description="Interest amount.",
        min_value=0,
    ),
    "Surcharge": FieldDefinition(
        name="Surcharge",
        field_type=FieldType.NUMBER,
        required=RequiredLevel.YES,
        description="Surcharge amount.",
        min_value=0,
    ),
    "total": FieldDefinition(
        name="total",
        field_type=FieldType.NUMBER,
        required=RequiredLevel.YES,
        description="Total = amount + Surcharge + Interest - discount.",
        min_value=0,
        auto_calculate="amount + Surcharge + Interest - discount",
    ),
    "type": FieldDefinition(
        name="type",
        field_type=FieldType.ENUM,
        required=RequiredLevel.YES,
        description="Fee type: LICENSE, PERMIT, SANITARY, GARBAGE, FIXED, OTHER.",
        enum_values=["LICENSE", "PERMIT", "SANITARY", "GARBAGE", "FIXED", "OTHER"],
    ),
    "qtr_from": FieldDefinition(
        name="qtr_from",
        field_type=FieldType.INTEGER,
        required=RequiredLevel.YES,
        description="Starting quarter. Accepted values: 1,2,3,4.",
        min_value=1,
        max_value=4,
    ),
    "qtr_to": FieldDefinition(
        name="qtr_to",
        field_type=FieldType.INTEGER,
        required=RequiredLevel.YES,
        description="Ending quarter. Must be >= qtr_from. Accepted values: 1,2,3,4.",
        min_value=1,
        max_value=4,
    ),
    "year": FieldDefinition(
        name="year",
        field_type=FieldType.INTEGER,
        required=RequiredLevel.YES,
        description="Payment year. 4-digit integer.",
        min_value=2000,
        max_value=2100,
    ),
}

# ============================================================
# Master Schema Registry
# ============================================================
SHEET_SCHEMAS = {
    "BPLS-Business": BPLS_BUSINESS_SCHEMA,
    "BPLS-Business Activity": BPLS_BUSINESS_ACTIVITY_SCHEMA,
    "BPLS-Application": BPLS_APPLICATION_SCHEMA,
    "BPLS-Application Fee": BPLS_APPLICATION_FEE_SCHEMA,
}

# ============================================================
# Conditional Validation Rules (from Excel)
# ============================================================
CONDITIONAL_RULES = {
    "BPLS-Business": [
        # DTI required when business_type = SOLE PROPRIETORSHIP
        {
            "field": "dti_no",
            "condition": {"field": "business_type", "value": "SOLE PROPRIETORSHIP"},
            "required": True,
        },
        {
            "field": "dti_registratrion_expiry_date",
            "condition": {"field": "business_type", "value": "SOLE PROPRIETORSHIP"},
            "required": True,
        },
        # SEC required when business_type = ONE PERSON CORPORATION, PARTNERSHIP, or CORPORATION
        {
            "field": "sec_no",
            "condition": {
                "field": "business_type",
                "value_in": [
                    "ONE PERSON CORPORATION",
                    "PARTNERSHIP",
                    "CORPORATION",
                ],
            },
            "required": True,
        },
        # CDA required when business_type = COOPERATIVE
        {
            "field": "cda_no",
            "condition": {"field": "business_type", "value": "COOPERATIVE"},
            "required": True,
        },
        # TDN/PIN required when location_owned = 1 (owned)
        {
            "field": "tdn_no",
            "condition": {"field": "location_owned", "value": 1},
            "required": True,
        },
        {
            "field": "pin_no",
            "condition": {"field": "location_owned", "value": 1},
            "required": True,
            "alternative_field": "tdn_no",
        },
        # Lessor/rental required when location_owned = 0 (rented)
        {
            "field": "lessor_name",
            "condition": {"field": "location_owned", "value": 0},
            "required": True,
        },
        {
            "field": "monthly_rental",
            "condition": {"field": "location_owned", "value": 0},
            "required": True,
        },
    ],
    "BPLS-Application": [
        {
            "field": "qtr_to",
            "condition": {"field": "qtr_from", "exists": True},
            "validation": "qtr_to >= qtr_from",
        },
    ],
    "BPLS-Application Fee": [
        {
            "field": "qtr_to",
            "condition": {"field": "qtr_from", "exists": True},
            "validation": "qtr_to >= qtr_from",
        },
    ],
}

# ============================================================
# Cross-field validation rules
# ============================================================
CROSS_FIELD_RULES = {
    "BPLS-Business": [
        {
            "field": "no_of_employees_residing_within_the_area",
            "validation": "no_of_employees_residing_within_the_area <= no_of_male_employees + no_of_female_employees",
            "message": "Employees within LGU must not exceed total employees (male + female)",
        },
    ],
}
