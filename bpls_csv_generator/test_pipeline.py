"""
Test Script - Creates sample Excel data and tests the full pipeline
"""

import os
import sys
from datetime import datetime, timedelta
import pandas as pd

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))


def create_sample_excel(filepath):
    """Create sample Excel file with test data"""

    print(f"📝 Creating sample test data: {filepath}")

    with pd.ExcelWriter(filepath, engine="openpyxl") as writer:

        # BPLS-Business Sheet
        business_data = [
            {
                "bin": "1400101-2024-0000001",
                "business_name": "Summit Solutions Co.",
                "trade_name": "The Horizon",
                "business_type": "CORPORATION",
                "dti_no": None,
                "dti_registration_expiry_date": None,
                "sec_no": "CS2024-12345",
                "cda_no": None,
                "tin_no": "123-456-789-00001",
                "email_address": "michaeljr.santos@email.com",
                "cellphone_no": "63917123456",
                "telephone_no": "8123-4567",
                "incharge_first_name": "Michael",
                "incharge_middle_name": "Reyes",
                "incharge_last_name": "Santos",
                "incharge_extension_name": "JR",
                "incharge_sex": "M",
                "incharge_country_of_citizenship": "Philippines",
                "incharge_street": "456 Main Avenue",
                "incharge_barangay": "Agtangao",
                "incharge_municipality": "Bangued",
                "incharge_province": "Abra",
                "office_street": "123 Elm Street, Unit 4B",
                "office_barangay_code": 1400101001,
                "location_owned": 1,
                "tdn_no": "TD-1234-5678-9012",
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
            {
                "bin": "1400101-2024-0000002",
                "business_name": "Juan's Sari-Sari Store",
                "trade_name": None,
                "business_type": "SOLE PROPRIETORSHIP",
                "dti_no": "2024-1234567",
                "dti_registration_expiry_date": datetime(2026, 3, 26),
                "sec_no": None,
                "cda_no": None,
                "tin_no": "987-654-321-00002",
                "email_address": "juan.store@email.com",
                "cellphone_no": "09171234568",  # Test auto-correction (09 -> 639)
                "telephone_no": None,
                "incharge_first_name": "Juan",
                "incharge_middle_name": "Dela",
                "incharge_last_name": "Cruz",
                "incharge_extension_name": None,
                "incharge_sex": "m",  # Test case correction
                "incharge_country_of_citizenship": "Philippines",
                "incharge_street": "789 Oak Road",
                "incharge_barangay": "Poblacion",
                "incharge_municipality": "Bangued",
                "incharge_province": "Abra",
                "office_street": "789 Oak Road",
                "office_barangay_code": 1400101002,
                "location_owned": 0,  # Rented
                "tdn_no": None,
                "pin_no": None,
                "lessor_name": "Alexandra Cruz",
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
        ]

        df_business = pd.DataFrame(business_data)
        df_business.to_excel(writer, sheet_name="BPLS-Business", index=False)

        # BPLS-Business Activity Sheet
        activity_data = [
            {
                "bin": "1400101-2024-0000001",
                "business_line_code": 47219,
                "capital_amount": 300000,
                "gross_amount": 10000,
                "gross_amount_essential": 5000,
                "gross_amount_nonessential": 5000,
                "retired_date": None,
            },
            {
                "bin": "1400101-2024-0000002",
                "business_line_code": 47110,
                "capital_amount": 50000,
                "gross_amount": 5000,
                "gross_amount_essential": 3000,
                "gross_amount_nonessential": 2000,
                "retired_date": datetime(2025, 12, 21),
            },
        ]

        df_activity = pd.DataFrame(activity_data)
        df_activity.to_excel(writer, sheet_name="BPLS-Business Activity", index=False)

        # BPLS-Application Sheet
        application_data = [
            {
                "business_bin": "1400101-2024-0000001",
                "application_type": "R",  # Renewal
                "application_date": datetime(2024, 1, 20),
                "year": 2024,
                "qtr_from": 1,
                "qtr_to": 4,
                "amount": 10000,
                "discount": 100,
                "surcharge": 2000,
                "interest": 0,
                "total": 11900,  # 10000 + 2000 + 0 - 100
                "issued_date": datetime(2024, 1, 20),
                "valid_until": datetime(2024, 12, 31),
                "or_no": "U12345678",
                "or_date": datetime(2024, 1, 20),
                "permit_no": "A-0001",
                "barangay_clearance_number": "ABC-123",
                "business_plate_number": "AA-0001",
                "mode_of_payment": "ONLINE",
            },
            {
                "business_bin": "1400101-2024-0000002",
                "application_type": "N",  # New
                "application_date": "01-15-2024",  # Test date format
                "year": 2024,
                "qtr_from": 1,
                "qtr_to": 4,
                "amount": 5000,
                "discount": 0,
                "surcharge": 500,
                "interest": 200,
                "total": 5700,  # 5000 + 500 + 200 - 0
                "issued_date": "2024-01-15",  # Test ISO date format
                "valid_until": "12/31/2024",
                "or_no": "U87654321",
                "or_date": datetime(2024, 1, 15),
                "permit_no": "A-0002",
                "barangay_clearance_number": None,
                "business_plate_number": "AA-0002",
                "mode_of_payment": "MANUAL",
            },
        ]

        df_application = pd.DataFrame(application_data)
        df_application.to_excel(writer, sheet_name="BPLS-Application", index=False)

        # BPLS-Application Fee Sheet
        fee_data = [
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
            {
                "business_bin": "1400101-2024-0000001",
                "application_or_no": "U12345678",
                "code": "LIC-01",
                "description": "Business License",
                "amount": 5000,
                "discount": 500,
                "Interest": 0,
                "Surcharge": 0,
                "total": 4500,
                "type": "LICENSE",
                "qtr_from": 1,
                "qtr_to": 4,
                "year": 2024,
            },
            {
                "business_bin": "1400101-2024-0000002",
                "application_or_no": "U87654321",
                "code": "SAN-01",
                "description": "Sanitary Permit",
                "amount": 1500,
                "discount": 0,
                "Interest": 100,
                "Surcharge": 200,
                "total": 1800,
                "type": "SANITARY",
                "qtr_from": 1,
                "qtr_to": 4,
                "year": 2024,
            },
        ]

        df_fee = pd.DataFrame(fee_data)
        df_fee.to_excel(writer, sheet_name="BPLS-Application Fee", index=False)

    print(f"✅ Sample data created: {filepath}")
    return filepath


def main():
    """Run test pipeline"""
    print("="*60)
    print("🧪 BPLS CSV Generator - Test Pipeline")
    print("="*60)
    print()

    # Create sample data
    test_dir = os.path.dirname(__file__)
    sample_file = os.path.join(test_dir, "test_data.xlsx")
    output_dir = os.path.join(test_dir, "test_outputs")

    create_sample_excel(sample_file)
    print()

    # Process the file
    print("="*60)
    print("🚀 Running Full Pipeline Test")
    print("="*60)
    print()

    from generators.csv_generator import BPLSCSVGenerator

    generator = BPLSCSVGenerator(output_dir)
    summary = generator.process_excel_file(sample_file, auto_correct=True)

    print()
    print("="*60)
    print("✅ TEST COMPLETE!")
    print("="*60)
    print(f"📊 Total rows processed: {summary['total_rows']}")
    print(f"📑 Sheets processed: {len(summary['sheets_processed'])}")
    print(f"❌ Errors found: {summary['total_errors']}")
    print(f"⚠️  Warnings: {summary['total_warnings']}")
    print(f"🔧 Auto-corrections: {summary['total_corrections']}")
    print(f"\n📁 Output files:")

    if os.path.exists(output_dir):
        for f in os.listdir(output_dir):
            filepath = os.path.join(output_dir, f)
            size = os.path.getsize(filepath)
            print(f"   - {f} ({size:,} bytes)")

    print()
    print("="*60)
    print("💡 Next Steps:")
    print("  1. Check the output files in test_outputs/")
    print("  2. Review validation_errors.csv for any issues")
    print("  3. Review transformation_log.csv for auto-corrections")
    print("  4. Start web UI: python main.py --web")
    print("="*60)


if __name__ == "__main__":
    main()
