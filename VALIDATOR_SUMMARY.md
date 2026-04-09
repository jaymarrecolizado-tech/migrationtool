# BPLS CSV Validator - Summary

## Purpose
A comprehensive CSV validation application that checks and corrects data based on migration rules from an Excel file.

## Features
1. **Validation Engine**: Validates CSV files against rules from "migration rules.xlsx"
2. **Automatic Correction**: Fixes common formatting issues (extra spaces, case, etc.)
3. **Detailed Reporting**: Shows errors, warnings, and corrections made
4. **Batch Processing**: Can validate multiple files (via command line)
5. **Output Generation**: Creates validated CSV files ready for migration

## How It Works

1. **Load Rules**: Reads validation rules from Excel file (4 sheets: BPLS-Business, BPLS-Business Activity, BPLS-Application, BPLS-Application Fee)
2. **Parse CSV**: Reads CSV file with proper encoding
3. **Row-by-Row Validation**: Checks each field against its rules
4. **Error Detection**: Identifies missing required fields, format violations, and conditional dependencies
5. **Automatic Correction**: Fixes simple issues like extra spaces, case conversion, etc.
6. **Report Generation**: Provides detailed console output and optional CSV output

## Validation Rules Supported

- **Required Fields**: Checks if mandatory fields are present
- **Conditional Requirements**: Field required based on other field values (e.g., DTI no required for Sole Proprietorship)
- **Format Validation**: 
  - BIN (Business Identification Number): 7-4-7 digit format
  - TIN: 000-000-000-00000 format
  - Email: Valid email format
  - Phone: Must start with 639
  - Business Type: Must be one of accepted values
  - DTI No: YEAR-7DIGITS format
  - SEC No: CS/PnYEAR-5TO7DIGITS format
  - CDA No: 9520-REGION-XXX-XXXX format
  - Sex: M or F only
  - Dates: MM/DD/YYYY format
  - Booleans: 1/0, true/false, yes/no
  - Character limits (min/max)
  - Alphanumeric with special characters

## Usage

### Command Line
```bash
python bpls_validator.py input.csv -o validated_output.csv
```

### Batch File
Double-click `validate.bat` for easy execution.

## Output

The validator produces:
- Console report with errors, warnings, and corrections
- Validated CSV file (if output path specified)

## Example Validation Results

```
VALIDATION RESULTS
================================================================================
Total rows processed: 100
Rows corrected: 5
Rows with errors: 2
Rows with warnings: 0

ERRORS:
  Row 3: Field 'dti_no' format error: Must be in format: YEAR-7DIGITS
  Row 7: Field 'email_address' format error: Must be a valid email address

CORRECTED FIELDS:
  Row 5: business_name changed from 'ABC  STORE' to 'ABC STORE'
```

## Files Included

1. `bpls_validator.py` - Main validator application
2. `validate.bat` - Batch file for easy execution
3. `migration rules.xlsx` - Validation rules (must be in same directory)
4. `README.md` - Complete documentation

## Error Handling

The validator identifies three types of issues:
- **Errors**: Critical issues that must be fixed before migration
- **Warnings**: Non-critical issues that should be reviewed
- **Corrections**: Automatic fixes applied to improve data quality

## Next Steps

1. Place your CSV file in the same directory as the validator
2. Run the validator using the batch file or command line
3. Review the error report
4. Fix any critical errors in your source data
5. Re-run validator to confirm all issues resolved
6. Use the validated CSV file for migration

## Limitations

- Does not handle complex data transformations beyond simple corrections
- Relies on rules defined in the Excel file
- Requires Python 3.8+ with pandas, openpyxl, numpy installed

## Installation

1. Install Python 3.8 or higher
2. Install required packages:
   ```
   pip install pandas openpyxl numpy
   ```
3. Place all files in the same directory
4. Run the validator!

## Support

For questions or issues, please refer to the README file or contact the developer.

## License

This validator is provided as-is for BPLS data migration validation.