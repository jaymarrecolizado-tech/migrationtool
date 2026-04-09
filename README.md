# BPLS CSV Validator

This is a Python application that validates and corrects CSV files based on migration rules from an Excel file.

## Features
- Validates CSV files against BPLS migration rules
- Corrects common formatting issues automatically
- Provides detailed error and warning reports
- Generates validated CSV output for migration

## Requirements

- Python 3.8+
- Required packages: pandas, openpyxl, numpy

## Installation

1. Install Python 3.8 or higher if not already installed.

2. Install required packages by running:
   ```
   pip install pandas openpyxl numpy
   ```

## Usage

### Basic Usage
```
python bpls_validator.py <csv_file> -o <output_file>
```

Example:
```
python bpls_validator.py "sample data/data.csv" -o "validated/data_validated.csv"
```

### Command-line Options
- `-r`, `--rules`: Path to Excel file with validation rules (default: migration rules.xlsx)
- `-o`, `--output`: Path to output validated CSV file

### Batch File
For easy execution, use the provided `validate.bat`:
1. Double-click `validate.bat`
2. Follow the prompts to enter CSV file path and output path

## Validation Rules

The validator uses rules from the Excel file "migration rules.xlsx" which contains multiple sheets:
- BPLS-Business: Business master data validation
- BPLS-Business Activity: Business activity/line validation  
- BPLS-Application: Application/transaction validation
- BPLS-Application Fee: Fee validation

Each field has validation criteria including:
- Required/conditional requirements
- Format validation (email, phone, BIN, TIN, etc.)
- Conditional dependencies between fields
- Character limits and patterns

## Error Handling

The validator will:
- Identify rows with errors and provide specific error messages
- Identify rows with warnings (non-critical issues)
- Automatically correct common formatting issues (extra spaces, case, etc.)
- Generate a detailed report of all issues

## Output

The validator generates:
- Validated CSV file with corrected data (if output path provided)
- Console report showing:
  - Total rows processed
  - Rows corrected
  - Rows with errors
  - Rows with warnings
  - Specific error messages for each row

## Example Output

```
Validating sample data/data.csv...
================================================================================
VALIDATION RESULTS
================================================================================
Total rows processed: 100
Rows corrected: 5
Rows with errors: 2
Rows with warnings: 1

ERRORS:
  Row 3: Field 'dti_no' format error: Must be in format: YEAR-7DIGITS
  Row 7: Field 'email_address' format error: Must be a valid email address

CORRECTED FIELDS:
  Row 5: business_name changed from 'ABC  STORE' to 'ABC STORE'
  Row 12: cellphone_no changed from '639123456789' to '639123456789'

Validation FAILED - Please fix the errors above.
```

## Tips

1. Always validate your CSV file before migration
2. Fix critical errors before proceeding
3. Use the validated CSV file for migration
4. Keep a backup of original data

## Troubleshooting

If you encounter issues:

1. "Rules file not found": Make sure migration rules.xlsx is in the same directory as the validator script
2. "CSV file not found": Check the CSV file path
3. "Module not found" errors: Install required packages with pip install pandas openpyxl numpy

## License

This validator is provided as-is for BPLS data migration validation.