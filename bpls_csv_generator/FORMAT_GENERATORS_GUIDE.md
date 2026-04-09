# 🏢 BPLS CSV Format Generators - 4 Independent Generators

## Overview

The BPLS Migration Tool now has **4 separate, independent format generators** - one for each sheet in the migration Excel file. Each generator is a standalone module that can validate, clean, and format data for its specific sheet.

---

## 📋 The 4 Format Generators

| # | Generator | Sheet | Fields | Icon |
|---|-----------|-------|--------|------|
| 1 | **BPLSBusinessFormatGenerator** | BPLS-Business | 37 fields | 🏢 |
| 2 | **BPLSBusinessActivityFormatGenerator** | BPLS-Business Activity | 8 fields | 📊 |
| 3 | **BPLSApplicationFormatGenerator** | BPLS-Application | 19 fields | 📝 |
| 4 | **BPLSApplicationFeeFormatGenerator** | BPLS-Application Fee | 13 fields | 💰 |

---

## 🏗️ Architecture

```
bpls_csv_generator/
├── generators/
│   ├── bpls_business_generator.py          # Generator 1: Business
│   ├── bpls_business_activity_generator.py # Generator 2: Business Activity
│   ├── bpls_application_generator.py        # Generator 3: Application
│   ├── bpls_application_fee_generator.py   # Generator 4: Application Fee
│   └── format_generators.py                # Export all generators
├── config/
│   └── schema.py                           # Schema for all 4 sheets
├── validators/                             # Validation logic
├── cleaners/                               # Auto-correction logic
└── test_all_generators.py                  # Test all 4 generators
```

---

## 🚀 Usage Examples

### Run All 4 Generators

```bash
python test_all_generators.py
```

This processes all 4 sheets from your Excel file and generates:
- `BPLS-Business_validated.csv` (37 rows)
- `BPLS-Business Activity_validated.csv` (8 rows)
- `BPLS-Application_validated.csv` (19 rows)
- `BPLS-Application Fee_validated.csv` (13 rows)

### Use Individual Generators in Code

```python
from generators.format_generators import (
    BPLSBusinessFormatGenerator,
    BPLSBusinessActivityFormatGenerator,
    BPLSApplicationFormatGenerator,
    BPLSApplicationFeeFormatGenerator,
)

# Generator 1: Business
gen1 = BPLSBusinessFormatGenerator("./outputs")
summary1 = gen1.process("migration rules.xlsx", auto_correct=True)

# Generator 2: Business Activity
gen2 = BPLSBusinessActivityFormatGenerator("./outputs")
summary2 = gen2.process("migration rules.xlsx", auto_correct=True)

# Generator 3: Application
gen3 = BPLSApplicationFormatGenerator("./outputs")
summary3 = gen3.process("migration rules.xlsx", auto_correct=True)

# Generator 4: Application Fee
gen4 = BPLSApplicationFeeFormatGenerator("./outputs")
summary4 = gen4.process("migration rules.xlsx", auto_correct=True)
```

---

## 📊 Output Per Generator

Each generator produces:

### Validated CSV
- `{SheetName}_validated.csv` - Clean, formatted data ready for import

### Error Reports
- `{SheetName}_errors.csv` - Validation errors with row numbers and suggestions

### Transformation Logs
- `{SheetName}_transformations.csv` - Auto-corrections applied

---

## 🔧 Generator 1: BPLS-Business

**Fields Validated:** 37 fields

| Category | Fields | Validations |
|----------|--------|-------------|
| **BIN** | bin | Format: PSGC(7)-YEAR(4)-INCREMENT(7) |
| **Names** | business_name, trade_name | 3-100 chars, alphanumeric |
| **Type** | business_type | Enum: 5 allowed values |
| **Registration** | dti_no, sec_no, cda_no | Conditional based on type |
| **Dates** | dti_registration_expiry_date | MM/DD/YYYY format |
| **Contact** | email_address, cellphone_no | Email format, phone format |
| **Person** | incharge_* fields | String, enum (M/F) |
| **Address** | office_* fields | String, integer codes |
| **Location** | location_owned, tdn_no, pin_no | Boolean, conditional |
| **Financial** | monthly_rental, area | Numbers ≥ 0 |
| **Employees** | no_of_* fields | Integers ≥ 0 |
| **Vehicles** | no_of_van/truck/motorcycle | Integers ≥ 0 |

**Conditional Rules:**
- If `business_type = SOLE PROPRIETORSHIP` → `dti_no` and `dti_registration_expiry_date` required
- If `business_type = CORPORATION/PARTNERSHIP` → `sec_no` required
- If `business_type = COOPERATIVE` → `cda_no` required
- If `location_owned = 1` → `tdn_no` or `pin_no` required
- If `location_owned = 0` → `lessor_name` and `monthly_rental` required

---

## 📊 Generator 2: BPLS-Business Activity

**Fields Validated:** 8 fields

| Field | Type | Validation |
|-------|------|------------|
| bin | BIN | Must exist in BPLS-Business |
| business_line_code | Integer | Must exist in system |
| capital_amount | Number | ≥ 0 |
| gross_amount | Number | ≥ 0 |
| gross_amount_essential | Number | ≥ 0 |
| gross_amount_nonessential | Number | ≥ 0 |
| retired_date | Date | MM/DD/YYYY (optional) |

---

## 📝 Generator 3: BPLS-Application

**Fields Validated:** 19 fields

| Field | Type | Validation |
|-------|------|------------|
| business_bin | BIN | Must exist in BPLS-Business |
| application_type | Enum | N (New), R (Renewal), Q (Quarterly) |
| application_date | Date | MM/DD/YYYY |
| year | Integer | 4 digits (YYYY) |
| qtr_from, qtr_to | Integer | 1-4, qtr_to ≥ qtr_from |
| amount | Number | ≥ 0 |
| discount | Number | ≥ 0 |
| surcharge | Number | ≥ 0 |
| interest | Number | ≥ 0 |
| total | Number | Calculated: amount + surcharge + interest - discount |
| issued_date | Date | MM/DD/YYYY |
| valid_until | Date | MM/DD/YYYY |
| or_no | String | Alphanumeric, unique |
| or_date | Date | MM/DD/YYYY |
| permit_no | String | Alphanumeric (optional) |
| barangay_clearance_number | String | Alphanumeric (optional) |
| business_plate_number | String | Alphanumeric (optional) |
| mode_of_payment | Enum | ONLINE or MANUAL |

**Conditional Rules:**
- If `qtr_from` exists → `qtr_to >= qtr_from`

---

## 💰 Generator 4: BPLS-Application Fee

**Fields Validated:** 13 fields

| Field | Type | Validation |
|-------|------|------------|
| business_bin | BIN | Must exist in BPLS-Business |
| application_or_no | String | Must exist in BPLS-Application |
| code | String | 2-20 chars |
| description | String | 2-100 chars |
| amount | Number | ≥ 0 |
| discount | Number | ≥ 0 |
| Interest | Number | ≥ 0 |
| Surcharge | Number | ≥ 0 |
| total | Number | Calculated: amount + Surcharge + Interest - discount |
| type | Enum | LICENSE, PERMIT, SANITARY, GARBAGE, FIXED, OTHER |
| qtr_from | Integer | 1-4 |
| qtr_to | Integer | 1-4, qtr_to ≥ qtr_from |
| year | Integer | 4 digits |

**Conditional Rules:**
- If `qtr_from` exists → `qtr_to >= qtr_from`

---

## 📊 Test Results

All 4 generators tested successfully:

```
✅ ALL 4 FORMAT GENERATORS TESTED SUCCESSFULLY!

📊 Total rows processed: 77
❌ Total errors found: 0
⚠️  Total warnings: 0
🔧 Total auto-corrections: 0

📁 Generated Files:
  ✓ BPLS-Business: 37 rows, 0 errors
  ✓ BPLS-Business Activity: 8 rows, 0 errors
  ✓ BPLS-Application: 19 rows, 0 errors
  ✓ BPLS-Application Fee: 13 rows, 0 errors
```

---

## 🎯 Benefits of Separate Generators

1. **Independent Processing** - Run any generator independently
2. **Targeted Validation** - Each generator has sheet-specific rules
3. **Parallel Execution** - Can process all 4 sheets simultaneously
4. **Isolated Errors** - Issues in one sheet don't affect others
5. **Modular Design** - Easy to add new sheets or modify existing ones
6. **Clear Reports** - Each sheet gets its own error/transformation logs

---

## 🔌 Integration

All generators share:
- **Same validators** from `validators/` package
- **Same cleaners** from `cleaners/` package
- **Same schema** from `config/schema.py`
- **Same output format** (CSV with UTF-8 BOM)

---

## 📁 File Locations

**Generators:** `C:\Users\DICT\Desktop\RULES\bpls_csv_generator\generators\`
**Test Script:** `C:\Users\DICT\Desktop\RULES\bpls_csv_generator\test_all_generators.py`
**Outputs:** `C:\Users\DICT\Desktop\RULES\bpls_csv_generator\test_outputs\`

---

**4 Independent Format Generators - Ready for Production! 🎉**
