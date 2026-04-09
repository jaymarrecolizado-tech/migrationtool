"""
Foolproof Test - Creates sample data WITH intentional errors to verify validation
"""

import os
import sys
from datetime import datetime
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))

from generators.format_generators import (
    BPLSBusinessFormatGenerator,
    BPLSBusinessActivityFormatGenerator,
    BPLSApplicationFormatGenerator,
    BPLSApplicationFeeFormatGenerator,
)


def create_test_data_with_errors(filepath):
    """Create test Excel file WITH intentional errors to test validation"""
    
    print("📝 Creating test data WITH intentional errors...")
    print()

    with pd.ExcelWriter(filepath, engine="openpyxl") as writer:

        # BPLS-Business with intentional errors
        business_data = [
            # Row 1: Valid corporation
            {
                "bin": "1400101-2024-0000001",
                "business_name": "Summit Solutions Co.",
                "trade_name": "The Horizon",
                "business_type": "CORPORATION",
                "dti_no": None,  # Not required for corporation
                "dti_registration_expiry_date": None,
                "sec_no": "CS2024-12345",
                "cda_no": None,
                "tin_no": "123-456-789-00001",
                "email_address": "contact@summit.com",
                "cellphone_no": "63917123456",
                "telephone_no": "8123-4567",
                "incharge_first_name": "Michael",
                "incharge_middle_name": "Reyes",
                "incharge_last_name": "Santos",
                "incharge_extension_name": "JR",
                "incharge_sex": "M",
                "incharge_country_of_citizenship": "Philippines",
                "incharge_street": "456 Main Ave",
                "incharge_barangay": "Agtangao",
                "incharge_municipality": "Bangued",
                "incharge_province": "Abra",
                "office_street": "123 Elm St",
                "office_barangay_code": 1400101001,
                "location_owned": 1,
                "tdn_no": "TD-1234-5678",
                "pin_no": None,
                "lessor_name": None,
                "monthly_rental": None,
                "area": 100,
                "no_of_male_employees": 10,
                "no_of_female_employees": 5,
                "no_of_employees_residing_within_the_area": 8,
                "no_of_van": 2,
                "no_of_truck": 0,
                "no_of_motorcycle": 2,
                "activity_type": "Main Office",
            },
            # Row 2: ERROR - Sole proprietorship missing DTI (should fail validation)
            {
                "bin": "1400101-2024-0000002",
                "business_name": "Juan Store",
                "trade_name": None,
                "business_type": "SOLE PROPRIETORSHIP",
                "dti_no": None,  # ❌ ERROR: Required for sole prop
                "dti_registration_expiry_date": None,  # ❌ ERROR: Required for sole prop
                "sec_no": None,
                "cda_no": None,
                "tin_no": None,
                "email_address": "juan@email.com",
                "cellphone_no": "09171234568",  # Will auto-correct to 639
                "telephone_no": None,
                "incharge_first_name": "Juan",
                "incharge_middle_name": "Dela",
                "incharge_last_name": "Cruz",
                "incharge_extension_name": None,
                "incharge_sex": "m",  # Will auto-correct to M
                "incharge_country_of_citizenship": "Philippines",
                "incharge_street": "789 Oak Rd",
                "incharge_barangay": "Poblacion",
                "incharge_municipality": "Bangued",
                "incharge_province": "Abra",
                "office_street": "789 Oak Rd",
                "office_barangay_code": 1400101002,
                "location_owned": 0,
                "tdn_no": None,
                "pin_no": None,
                "lessor_name": "Alex Cruz",
                "monthly_rental": 15000,
                "area": 50,
                "no_of_male_employees": 2,
                "no_of_female_employees": 1,
                "no_of_employees_residing_within_the_area": 3,
                "no_of_van": 0,
                "no_of_truck": 0,
                "no_of_motorcycle": 1,
                "activity_type": "Main Office",
            },
            # Row 3: ERROR - Invalid business type
            {
                "bin": "1400101-2024-0000003",
                "business_name": "Test Business",
                "trade_name": None,
                "business_type": "INVALID TYPE",  # ❌ ERROR: Not in enum
                "dti_no": None,
                "dti_registration_expiry_date": None,
                "sec_no": None,
                "cda_no": None,
                "tin_no": None,
                "email_address": "invalid-email",  # ❌ ERROR: Invalid email
                "cellphone_no": "12345",  # ❌ ERROR: Invalid phone
                "telephone_no": None,
                "incharge_first_name": "Test",
                "incharge_middle_name": None,
                "incharge_last_name": "User",
                "incharge_extension_name": None,
                "incharge_sex": "X",  # ❌ ERROR: Must be M or F
                "incharge_country_of_citizenship": "Philippines",
                "incharge_street": None,
                "incharge_barangay": "Barangay1",
                "incharge_municipality": "Test",
                "incharge_province": "Test",
                "office_street": None,
                "office_barangay_code": 1400101003,
                "location_owned": 1,
                "tdn_no": None,  # ❌ ERROR: Required when owned
                "pin_no": None,  # ❌ ERROR: Required when owned
                "lessor_name": None,
                "monthly_rental": None,
                "area": -10,  # ❌ ERROR: Negative area
                "no_of_male_employees": -5,  # ❌ ERROR: Negative employees
                "no_of_female_employees": 0,
                "no_of_employees_residing_within_the_area": 0,
                "no_of_van": 0,
                "no_of_truck": 0,
                "no_of_motorcycle": 0,
                "activity_type": "Office",
            },
            # Row 4: Valid cooperative
            {
                "bin": "1400101-2024-0000004",
                "business_name": "Workers Cooperative",
                "trade_name": "Coop Store",
                "business_type": "COOPERATIVE",
                "dti_no": None,
                "dti_registration_expiry_date": None,
                "sec_no": None,
                "cda_no": "9520-16012345",  # Required for cooperative
                "cda_no": "9520-16012345",
                "tin_no": None,
                "email_address": "coop@email.com",
                "cellphone_no": "63918123456",
                "telephone_no": None,
                "incharge_first_name": "Maria",
                "incharge_middle_name": "Santos",
                "incharge_last_name": "Reyes",
                "incharge_extension_name": None,
                "incharge_sex": "F",
                "incharge_country_of_citizenship": "Philippines",
                "incharge_street": "456 Pine St",
                "incharge_barangay": "Barangay2",
                "incharge_municipality": "Test",
                "incharge_province": "Test",
                "office_street": "456 Pine St",
                "office_barangay_code": 1400101004,
                "location_owned": 1,
                "tdn_no": "TD-9999",
                "pin_no": "99-99-99",
                "lessor_name": None,
                "monthly_rental": None,
                "area": 200,
                "no_of_male_employees": 15,
                "no_of_female_employees": 20,
                "no_of_employees_residing_within_the_area": 30,
                "no_of_van": 3,
                "no_of_truck": 1,
                "no_of_motorcycle": 0,
                "activity_type": "Main Office",
            },
        ]

        df_business = pd.DataFrame(business_data)
        df_business.to_excel(writer, sheet_name="BPLS-Business", index=False)

        # BPLS-Business Activity with errors
        activity_data = [
            # Valid activity
            {
                "bin": "1400101-2024-0000001",
                "business_line_code": 47219,
                "capital_amount": 300000,
                "gross_amount": 10000,
                "gross_amount_essential": 5000,
                "gross_amount_nonessential": 5000,
                "retired_date": None,
            },
            # ERROR - BIN doesn't exist in Business
            {
                "bin": "9999999-9999-9999999",  # ❌ ERROR: Invalid BIN
                "business_line_code": 47110,
                "capital_amount": 50000,
                "gross_amount": 5000,
                "gross_amount_essential": 3000,
                "gross_amount_nonessential": 2000,
                "retired_date": None,
            },
            # ERROR - Negative capital
            {
                "bin": "1400101-2024-0000001",
                "business_line_code": 47110,
                "capital_amount": -1000,  # ❌ ERROR: Negative
                "gross_amount": 5000,
                "gross_amount_essential": 3000,
                "gross_amount_nonessential": 2000,
                "retired_date": "13/45/2024",  # ❌ ERROR: Invalid date
            },
        ]

        df_activity = pd.DataFrame(activity_data)
        df_activity.to_excel(writer, sheet_name="BPLS-Business Activity", index=False)

        # BPLS-Application with errors
        application_data = [
            # Valid application
            {
                "business_bin": "1400101-2024-0000001",
                "application_type": "R",
                "application_date": datetime(2024, 1, 20),
                "year": 2024,
                "qtr_from": 1,
                "qtr_to": 4,
                "amount": 10000,
                "discount": 100,
                "surcharge": 2000,
                "interest": 0,
                "total": 11900,
                "issued_date": datetime(2024, 1, 20),
                "valid_until": datetime(2024, 12, 31),
                "or_no": "U12345678",
                "or_date": datetime(2024, 1, 20),
                "permit_no": "A-0001",
                "barangay_clearance_number": "ABC-123",
                "business_plate_number": "AA-0001",
                "mode_of_payment": "ONLINE",
            },
            # ERROR - Invalid application type
            {
                "business_bin": "1400101-2024-0000001",
                "application_type": "X",  # ❌ ERROR: Invalid type
                "application_date": "2024/01/15",
                "year": 2024,
                "qtr_from": 4,
                "qtr_to": 1,  # ❌ ERROR: qtr_to < qtr_from
                "amount": 5000,
                "discount": 0,
                "surcharge": 500,
                "interest": 200,
                "total": 5000,  # ❌ ERROR: Wrong calculation (should be 5700)
                "issued_date": "2024-01-15",
                "valid_until": "12/31/2024",
                "or_no": "U87654321",
                "or_date": datetime(2024, 1, 15),
                "permit_no": "A-0002",
                "barangay_clearance_number": None,
                "business_plate_number": "AA-0002",
                "mode_of_payment": "INVALID",  # ❌ ERROR: Invalid enum
            },
        ]

        df_application = pd.DataFrame(application_data)
        df_application.to_excel(writer, sheet_name="BPLS-Application", index=False)

        # BPLS-Application Fee with errors
        fee_data = [
            # Valid fee
            {
                "business_bin": "1400101-2024-0000001",
                "application_or_no": "U12345678",
                "code": "GF-01",
                "description": "Garbage Fee",
                "amount": 3000,
                "discount": 0,
                "Interest": 0,
                "Surcharge": 0,
                "total": 3000,
                "type": "GARBAGE",
                "qtr_from": 1,
                "qtr_to": 4,
                "year": 2024,
            },
            # ERROR - OR doesn't exist
            {
                "business_bin": "1400101-2024-0000001",
                "application_or_no": "U99999999",  # ❌ ERROR: OR not in Application
                "code": "X",  # ❌ ERROR: Too short (min 2 chars)
                "description": "X",  # ❌ ERROR: Too short
                "amount": -500,  # ❌ ERROR: Negative
                "discount": 0,
                "Interest": 0,
                "Surcharge": 0,
                "total": -500,  # ❌ ERROR: Negative
                "type": "INVALID TYPE",  # ❌ ERROR: Invalid enum
                "qtr_from": 5,  # ❌ ERROR: Quarter must be 1-4
                "qtr_to": 1,  # ❌ ERROR: qtr_to < qtr_from
                "year": 2024,
            },
        ]

        df_fee = pd.DataFrame(fee_data)
        df_fee.to_excel(writer, sheet_name="BPLS-Application Fee", index=False)

    print("✅ Test data created with intentional errors")
    print()


def main():
    """Run foolproof test"""
    print("="*70)
    print("🧪 FOOLPROOF TEST - Testing Validation with Intentional Errors")
    print("="*70)
    print()

    # Create test data with errors
    test_dir = os.path.dirname(__file__)
    test_file = os.path.join(test_dir, "foolproof_test_data.xlsx")
    output_dir = os.path.join(test_dir, "foolproof_outputs")

    create_test_data_with_errors(test_file)

    # Test all 4 generators
    print("\n" + "="*70)
    print("🚀 Running All 4 Format Generators")
    print("="*70)

    gen1 = BPLSBusinessFormatGenerator(output_dir)
    summary1 = gen1.process(test_file, auto_correct=True)

    print("\n\n")
    gen2 = BPLSBusinessActivityFormatGenerator(output_dir)
    summary2 = gen2.process(test_file, auto_correct=True)

    print("\n\n")
    gen3 = BPLSApplicationFormatGenerator(output_dir)
    summary3 = gen3.process(test_file, auto_correct=True)

    print("\n\n")
    gen4 = BPLSApplicationFeeFormatGenerator(output_dir)
    summary4 = gen4.process(test_file, auto_correct=True)

    # Final Summary
    print("\n\n")
    print("="*70)
    print("✅ FOOLPROOF TEST COMPLETE!")
    print("="*70)
    print()

    summaries = [summary1, summary2, summary3, summary4]

    total_rows = sum(s["total_rows"] for s in summaries)
    total_errors = sum(s["total_errors"] for s in summaries)
    total_warnings = sum(s["total_warnings"] for s in summaries)
    total_corrections = sum(s["total_corrections"] for s in summaries)

    print(f"📊 Total rows processed: {total_rows}")
    print(f"❌ Total errors found: {total_errors}")
    print(f"⚠️  Total warnings: {total_warnings}")
    print(f"🔧 Total auto-corrections: {total_corrections}")
    print()

    print("📁 Generated Validated CSVs:")
    print("-" * 70)
    for s in summaries:
        status = "✅ PASS" if s["total_errors"] == 0 else f"❌ {s['total_errors']} ERRORS"
        print(f"  {status} | {s['sheet']}: {s['output_file']}")

    print()
    print("="*70)
    print("💡 Output files:")
    print(f"   {os.path.abspath(output_dir)}")
    print()
    print("📋 Check these files:")
    print("   - *_validated.csv - Clean data ready for import")
    print("   - *_errors.csv - List of validation errors found")
    print("   - *_transformations.csv - Auto-corrections applied")
    print("="*70)


if __name__ == "__main__":
    main()
