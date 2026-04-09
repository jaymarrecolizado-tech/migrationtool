# BPLS CSV Validator - Enhanced Web Application

## 🎉 What's New

This enhanced validator includes all the features you requested:

### ✅ Key Features

1. **📁 Automatic Rule Detection**
   - The app reads your CSV headers and automatically determines which validation rules to apply
   - Supports all BPLS sheets:
     - BPLS-Business (master data)
     - BPLS-Business Activity (line items)
     - BPLS-Application (transactions)
     - BPLS-Application Fee (fees)
   - You don't need to manually specify which rules to use!

2. **🔍 Live Edit Mode**
   - Upload your CSV and see errors highlighted in a user-friendly table
   - Each error row shows:
     - Row number
     - Field name with error
     - The validation rule that was violated
     - Original value (with problem)
     - Suggested correction (when applicable)
   - Hover over any error cell to see the full rule explanation

3. **📊 Progress Dashboard**
   - Real-time statistics:
     - Total rows processed
     - Errors found count
     - Fields corrected count
   - Visual color coding (green = good, red = errors)

4. **🧹 Automatic Data Cleaning**
   - **ALL string fields are automatically trimmed** of:
     - Leading whitespace (spaces, tabs)
     - Trailing whitespace
     - Extra spaces between words
   - No manual trimming needed!

5. **💾 Edit Mode with Guidance**
   - When you see errors, the app tells you:
     - What the rule requires
     - Why your value is wrong
     - What the correct format looks like
   - You never have to guess or look up rules again!

6. **📥 Multiple Download Options**
   - **Download Original** - Get your original data back
   - **Apply Corrections & Download** - Get CSV with all auto-corrections applied
   - **Download Cleansed** - Get CSV with errors removed and formatting fixed

7. **🚀 Fast Performance**
   - Web-based interface - no need to run Python scripts manually
   - Upload files up to 16MB
   - Instant validation results
   - Download-ready outputs

---

## 🚀 How to Run

### Method 1: Quick Start (Recommended)

1. **Install dependencies:**
   ```bash
   pip install -r requirements_web.txt
   ```

2. **Start the web app:**
   ```bash
   python app_web.py
   ```

3. **Open your browser:**
   - Navigate to: `http://localhost:5000`

4. **Upload your CSV:**
   - Click the "Choose File" button
   - Select your CSV file

5. **Review results:**
   - See which rules were detected automatically
   - Review errors highlighted in red
   - Hover over error cells for rule details
   - Download corrected data

### Method 2: Using Original Script (Command Line)

If you prefer command line validation, you can still use the Python scripts:

```bash
# Basic validation
python bpls_validator.py "your_file.csv" -o "output.csv"

# Improved version (with whitespace trimming)
python bpls_validator_improved.py "your_file.csv" -o "output.csv"
```

---

## 📋 What Files Are Generated

When you use the web app, it can generate up to 3 files:

### 1. **original_data.csv**
   - Your exact uploaded data (with all whitespace)
   - Use this if you want to manually review or back up

### 2. **validated_data.csv**
   - Contains all auto-corrections applied
   - Errors are preserved (not auto-fixed)
   - All dates formatted as mm/dd/yyyy
   - Phones formatted with 639 prefix

### 3. **cleansed_data.csv**
   - Same as validated data PLUS:
   - Rows with errors are removed
   - Only clean rows included
   - Ready for migration without errors

---

## 🎨 Features Explained

### Automatic Rule Detection

The app looks at your CSV headers and matches them against known BPLS templates:

| If Your CSV Has... | Rules Applied |
|--------------------|---------------|
| `bin`, `business_name`, `business_type`, etc. | **BPLS-Business** (40 fields) |
| `bin`, `business_line_code`, `capital_amount`, etc. | **BPLS-Business Activity** (10 fields) |
| `business_bin`, `application_type`, `year`, etc. | **BPLS-Application** (21 fields) |
| `business_bin`, `code`, `amount`, `quarter` | **BPLS-Application Fee** (15 fields) |

### Error Display

Each error row shows:

```
Row 5 | Field: business_type
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Error: Must be one of: SOLE PROPRIETORSHIP; ONE PERSON CORPORATION; 
       PARTNERSHIP; CORPORATION; or COOPERATIVE
       
Rule: Accepted values: SOLE PROPRIETORSHIP; ONE PERSON CORPORATION; 
       PARTNERSHIP; CORPORATION; or COOPERATIVE
       
Original: "sole prop" (truncated)
Suggested: [Leave blank for auto-correction]
```

### Correction Types

The app applies these auto-corrections:

| Field Type | What Gets Fixed | Example |
|------------|----------------|---------|
| **BIN** | Hyphen positions and digit padding | `1400102024123` → `1400101-2024-0123` |
| **Email** | None (just validated) | Validated against regex |
| **Cellphone** | 639 prefix addition | `91234567` → `'63991234567'` |
| **Date** | Format and leading zeros | `3/26/2028` → `03/26/2028` |
| **Business Name** | Trailing spaces removed | `" Store "` → `"Store"` |

---

## 🔧 Configuration

### Edit These Variables in `app_web.py` (if needed):

```python
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload
app.config['UPLOAD_FOLDER'] = 'uploads'         # Where uploaded files go
app.config['CLEANSED_FOLDER'] = 'cleansed'     # Where output files go
```

### Excel Rules File

Ensure `migration rules.xlsx` is in the same directory as `app_web.py`.

---

## 📊 Validation Rules Summary

### BPLS-Business (40 Fields)

#### Identification
- **bin**: `PSGC (7digits) - YEAR (4digits) - INCREMENT (7digits)`
- **tin_no**: `000-000-000-00000` (12 digits)

#### Business Type
- Must be one of: `SOLE PROPRIETORSHIP`, `ONE PERSON CORPORATION`, `PARTNERSHIP`, `CORPORATION`, `COOPERATIVE`

#### Conditional Requirements

| Field | Required When Business Type Is... |
|-------|----------------------------------|
| `dti_no` | SOLE PROPRIETORSHIP |
| `sec_no` | ONE PERSON CORPORATION, PARTNERSHIP, or CORPORATION |
| `cda_no` | COOPERATIVE |

#### Dates
- Format: `MM/DD/YYYY`
- Leading zeros required for months 1-9
- Year range: 1900-2100

#### Phone
- **cellphone_no**: Must start with `639` (Philippines mobile)
- **telephone_no**: Optional, up to 20 characters

---

## 🐛 Troubleshooting

### "No rules found" error
- Make sure `migration rules.xlsx` is in the same folder as `app_web.py`
- Check that the Excel file contains sheets starting with "BPLS-"

### "Cannot read CSV file" error
- Ensure file is saved as CSV (comma-separated), not Excel
- Check file encoding (UTF-8 recommended)

### Web app won't start
- Install requirements: `pip install -r requirements_web.txt`
- Check if port 5000 is already in use: `netstat -an | findstr :5000`
- Try a different port if needed: Change `port=5000` in `app_web.py`

---

## 💡 Tips

1. **Test with small files first**: Try with 2-5 rows to see how it works
2. **Review all errors**: Even if validation passes, review warnings
3. **Download original**: Always keep a backup of your data
4. **Use cleansed for migration**: The cleansed file removes all error rows
5. **Edit in spreadsheet**: You can also edit in Excel/Google Sheets before uploading

---

## 📝 Contributing

**Contributor**: JE Lite

To contribute:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request with clear description

---

## 📄 License

This validator is provided as-is for BPLS data migration validation.
