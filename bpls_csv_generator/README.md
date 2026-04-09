# 🏢 BPLS CSV Format Generator

A comprehensive tool to validate, clean, and transform migration data for the **BPLS (Business Permit and Licensing System)**. This tool ensures your raw Excel data meets all format requirements before importing into the BPLS System.

---

## ✨ Features

### 🔍 **Multi-Pass Validation**
- **Schema Validation**: Validates column names, data types, and formats
- **Conditional Validation**: Enforces business rules (e.g., DTI required for Sole Proprietorship)
- **Cross-Sheet Validation**: Validates foreign key relationships between sheets
- **Data Integrity**: Auto-calculates derived fields (e.g., `total = amount + penalties - discount`)

### 🧹 **Auto-Correction**
Automatically fixes common data issues:
- Date formats → `MM/DD/YYYY`
- Phone numbers → `639XXXXXXXXX` (converts `09` prefix)
- Case normalization for enums
- Whitespace trimming
- Boolean normalization (`yes/no/true/false/1/0` → `1` or `0`)
- BIN format reconstruction

### 📊 **Comprehensive Reporting**
- `*_validated.csv` - Clean, ready-to-import CSV files
- `validation_errors.csv` - Detailed error log with suggestions
- `transformation_log.csv` - All auto-corrections applied
- `cross_sheet_errors.csv` - Foreign key validation issues
- `validation_summary.json` - Machine-readable summary

### 🌐 **Web Interface**
Beautiful, modern UI with:
- Drag-and-drop file upload
- Real-time processing progress
- Download all generated files
- Visual validation summary

---

## 🚀 Quick Start

### Installation

```bash
# Navigate to project directory
cd bpls_csv_generator

# Install dependencies
pip install -r requirements.txt
```

### Option 1: Web Interface (Recommended)

```bash
python main.py --web
```

Then open **http://localhost:5000** in your browser.

### Option 2: Command Line

```bash
# Process a file
python main.py "migration rules.xlsx"

# Process without auto-correction
python main.py "migration rules.xlsx" --no-auto-correct

# Custom output directory
python main.py "migration rules.xlsx" --output ./clean_csvs
```

### Option 3: Test Pipeline

```bash
# Run with sample data
python test_pipeline.py
```

---

## 📁 Project Structure

```
bpls_csv_generator/
├── config/
│   └── schema.py              # Field definitions & validation rules
├── validators/
│   ├── base.py                # Base validator class
│   ├── type_validators.py     # String, Number, Date, Enum, etc.
│   └── conditional.py         # Conditional validation rules
├── cleaners/
│   └── data_cleaners.py       # Auto-correction logic
├── generators/
│   ├── csv_generator.py       # Main orchestrator
│   └── cross_sheet_validator.py # Foreign key validation
├── templates/
│   └── index.html             # Web UI
├── static/
│   ├── css/style.css          # Web styles
│   └── js/app.js              # Web logic
├── uploads/                    # Uploaded files
├── outputs/                    # Generated CSVs & reports
├── main.py                     # CLI entry point
├── app.py                      # Flask web server
├── test_pipeline.py            # Test with sample data
└── requirements.txt            # Python dependencies
```

---

## 📋 Supported Sheets

### 1. **BPLS-Business** (35 fields)
Core business entity data including:
- BIN format validation (`PSGC-YEAR-INCREMENT`)
- Business type validation (Sole Proprietorship, Corporation, etc.)
- Conditional fields (DTI, SEC, CDA based on business type)
- Contact information (email, phone validation)
- Address and employee data

### 2. **BPLS-Business Activity** (7 fields)
Business line activities:
- BIN must exist in BPLS-Business
- Capital and gross amounts
- Optional retired date

### 3. **BPLS-Application** (19 fields)
Permit applications:
- Application type (N=New, R=Renewal, Q=Quarterly)
- Date validations
- Quarter validations (`qtr_to >= qtr_from`)
- Total calculation (`amount + surcharge + interest - discount`)
- Payment mode validation

### 4. **BPLS-Application Fee** (13 fields)
Fee breakdown:
- Foreign key to Application (OR number)
- Fee type validation (LICENSE, PERMIT, SANITARY, etc.)
- Total calculation
- Quarter validations

---

## 🔧 Configuration

### Edit Schema Rules

All validation rules are in `config/schema.py`. You can modify:

```python
# Add new field
"new_field": FieldDefinition(
    name="new_field",
    field_type=FieldType.STRING,
    required=RequiredLevel.YES,
    min_length=3,
    max_length=100,
)

# Add conditional rule
CONDITIONAL_RULES = {
    "BPLS-Business": [
        {
            "field": "new_field",
            "condition": {"field": "business_type", "value": "CORPORATION"},
            "required": True,
        },
    ],
}
```

### Add Custom Validators

Create new validators in `validators/type_validators.py`:

```python
class CustomValidator(BaseValidator):
    def validate(self, value, row_num, **kwargs):
        # Your validation logic
        return [ValidationResult(...)]

    def clean(self, value, **kwargs):
        # Your cleaning logic
        return cleaned_value, was_modified
```

---

## 📊 Output Files

### Validated CSVs
- `BPLS-Business_validated.csv`
- `BPLS-Business Activity_validated.csv`
- `BPLS-Application_validated.csv`
- `BPLS-Application Fee_validated.csv`

### Reports
- `validation_errors.csv` - All errors with row numbers and suggestions
- `transformation_log.csv` - Auto-corrections applied
- `cross_sheet_errors.csv` - Foreign key issues
- `validation_summary.json` - Overall statistics

---

## 🎯 Data Type Reference

| Type | Format | Example |
|------|--------|---------|
| **BIN** | `PSGC(7)-YEAR(4)-INCREMENT(7)` | `1400101-2024-0000001` |
| **Date** | `MM/DD/YYYY` | `01/15/2024` |
| **Phone** | `639XXXXXXXXX` | `63917123456` |
| **Email** | Standard email | `user@example.com` |
| **Enum** | Case-insensitive input | `CORPORATION`, `M`, `R` |
| **Boolean** | `1` or `0` | `1` (owned), `0` (rented) |
| **Number** | Numeric only | `10000`, `0` |
| **String** | Alphanumeric + special | `Summit Solutions Co.` |

---

## ⚠️ Common Issues & Solutions

### Issue: "Invalid date format"
**Solution**: Use `MM/DD/YYYY` format (e.g., `01/15/2024`). The tool auto-converts from:
- `2024-01-15` (ISO)
- `January 15, 2024`
- `01-15-2024`

### Issue: "Phone must start with 639"
**Solution**: Philippine mobile numbers must be in international format:
- ❌ `09171234567`
- ✅ `63917123456` (tool auto-converts)

### Issue: "Foreign key not found"
**Solution**: Ensure BIN/OR numbers in child sheets exist in parent sheets:
- `BPLS-Business Activity.bin` → must exist in `BPLS-Business.bin`
- `BPLS-Application.business_bin` → must exist in `BPLS-Business.bin`
- `BPLS-Application Fee.application_or_no` → must exist in `BPLS-Application.or_no`

### Issue: "Field is required when business_type = X"
**Solution**: Conditional fields based on business type:
- **SOLE PROPRIETORSHIP** → requires `dti_no` and `dti_registration_expiry_date`
- **CORPORATION/PARTNERSHIP** → requires `sec_no`
- **COOPERATIVE** → requires `cda_no`
- **location_owned = 1** → requires `tdn_no` or `pin_no`
- **location_owned = 0** → requires `lessor_name` and `monthly_rental`

---

## 🤝 Contributing

To add new validation rules or sheets:

1. Update `config/schema.py` with field definitions
2. Add validators in `validators/type_validators.py`
3. Add conditional rules in `CONDITIONAL_RULES`
4. Test with `python test_pipeline.py`

---

## 📞 Support

For issues or questions:
- Check `validation_errors.csv` for detailed error messages
- Review `transformation_log.csv` for auto-corrections
- Inspect `cross_sheet_errors.csv` for foreign key issues

---

## 📄 License

This tool is built for BPLS System migration data validation and format enforcement.

---

**Built with ❤️ for seamless data migration**
