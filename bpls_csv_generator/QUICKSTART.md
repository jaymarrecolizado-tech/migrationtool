# 🚀 Quick Start Guide - BPLS CSV Format Generator

## ✅ Installation Complete!

The tool is now ready to use. Here's how to get started:

---

## 📋 Option 1: Web Interface (RECOMMENDED)

### Start the Web Server

```bash
cd C:\Users\DICT\Desktop\RULES\bpls_csv_generator
python main.py --web
```

### Access the Interface

Open your browser and go to: **http://localhost:5000**

### Upload Your File

1. Drag & drop your Excel file onto the upload area
2. Or click "Browse Files" to select your file
3. Check/uncheck "Auto-Correct" (recommended: leave it checked)
4. Click "Process File"
5. Download all generated files

---

## 💻 Option 2: Command Line

### Process Your Migration File

```bash
cd C:\Users\DICT\Desktop\RULES\bpls_csv_generator

# Process your file
python main.py "C:\Users\DICT\Desktop\RULES\migration rules.xlsx"

# Custom output directory
python main.py "C:\Users\DICT\Desktop\RULES\migration rules.xlsx" --output ./my_outputs

# Without auto-correction (see all errors)
python main.py "C:\Users\DICT\Desktop\RULES\migration rules.xlsx" --no-auto-correct
```

---

## 📊 What Gets Generated

After processing, you'll get these files in the output directory:

### ✅ Validated CSV Files (Ready for Import)
- `BPLS-Business_validated.csv` - Clean business data
- `BPLS-Business Activity_validated.csv` - Clean business activities
- `BPLS-Application_validated.csv` - Clean applications
- `BPLS-Application Fee_validated.csv` - Clean application fees

### 📋 Validation Reports
- `validation_errors.csv` - All errors with row numbers and suggestions
- `transformation_log.csv` - All auto-corrections applied
- `cross_sheet_errors.csv` - Foreign key reference issues
- `validation_summary.json` - Machine-readable statistics

---

## 🔧 Auto-Corrections Performed

The tool automatically fixes:

| Issue | Example | Correction |
|-------|---------|------------|
| **Date format** | `2024-01-15` → | `01/15/2024` |
| **Phone prefix** | `09171234567` → | `639171234567` |
| **Case normalization** | `corporation` → | `CORPORATION` |
| **Whitespace** | `  John  ` → | `John` |
| **Boolean values** | `yes/true` → | `1` |
| **BIN format** | `140010120240000001` → | `1400101-2024-0000001` |
| **Email case** | `User@Email.COM` → | `user@email.com` |

---

## ⚠️ Common Errors & Fixes

### Error: "Field is required when business_type = X"

**Example**: DTI number missing for Sole Proprietorship

**Fix**: Add the required value based on business type:
- **SOLE PROPRIETORSHIP** → needs `dti_no` and `dti_registration_expiry_date`
- **CORPORATION** → needs `sec_no`
- **COOPERATIVE** → needs `cda_no`

### Error: "Invalid BIN format"

**Expected**: `1400101-2024-0000001` (PSGC-YEAR-INCREMENT)

**Fix**: Ensure BIN follows the 7-4-7 digit format with dashes

### Error: "Foreign key not found"

**Example**: `business_bin` in Application doesn't exist in Business sheet

**Fix**: Ensure all references match:
- Activity `bin` → must exist in Business `bin`
- Application `business_bin` → must exist in Business `bin`
- Application Fee `application_or_no` → must exist in Application `or_no`

### Error: "Phone must start with 639"

**Wrong**: `09171234567`
**Right**: `639171234567`

The tool auto-converts `09` to `639` if auto-correct is enabled.

---

## 🧪 Test the Tool

Run the built-in test to verify everything works:

```bash
python test_pipeline.py
```

This creates sample data and processes it through the full pipeline.

---

## 📁 Project Location

All files are in: `C:\Users\DICT\Desktop\RULES\bpls_csv_generator\`

```
bpls_csv_generator/
├── main.py                     # Main entry point
├── app.py                      # Web server
├── test_pipeline.py            # Test with sample data
├── test_migration.py           # Test with your migration file
├── requirements.txt            # Dependencies
├── config/
│   └── schema.py              # Validation rules (editable)
├── validators/                 # Data validators
├── cleaners/                   # Auto-correction logic
├── generators/                 # CSV generation
├── templates/                  # Web UI templates
├── static/                     # CSS and JS
├── uploads/                    # Uploaded files
├── outputs/                    # Generated CSVs
└── README.md                   # Full documentation
```

---

## 🎯 Next Steps

1. **Start the web interface**: `python main.py --web`
2. **Upload your migration Excel file**
3. **Review the validation results**
4. **Download the validated CSV files**
5. **Import into BPLS System**

---

## 📞 Need Help?

- Check `validation_errors.csv` for detailed error messages
- Review `transformation_log.csv` to see auto-corrections
- See `cross_sheet_errors.csv` for foreign key issues
- Read the full README.md for advanced usage

---

## 🔌 Stop the Server

Press `Ctrl+C` in the terminal to stop the web server.

---

**Ready to migrate! 🎉**
