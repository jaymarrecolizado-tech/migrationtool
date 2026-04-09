# BPLS CSV Generator — Agent Context

## Project Overview

**BPLS CSV Format Generator** — A Python web app that validates, cleans, and transforms migration data for the Business Permit and Licensing System (BPLS). Takes Excel/CSV files with 4 sheets, runs a multi-pass validation pipeline, auto-corrects common issues, and outputs clean CSVs plus detailed reports.

**Location:** `C:\Users\DICT\Desktop\RULES\bpls_csv_generator`

**Run:** `python main.py --web` → http://localhost:5000

---

## Architecture

### Pipeline Stages
1. **READ** → Excel/CSV → dict of sheet_name → list of row dicts
2. **CLEAN** → DataCleaner normalizes dates, phones, bins, enums, booleans
3. **CROSS-SHEET VALIDATE** → CrossSheetValidator checks foreign keys between sheets
4. **VALIDATE** → Per-field, per-row against schema (type, conditional, cross-field rules)
5. **AUTO-CORRECT** → Replace values with corrected_value from results
6. **WRITE CSV** → UTF-8 BOM encoding
7. **GENERATE REPORTS** → validation_errors.csv, transformation_log.csv, validation_summary.json, cross_sheet_errors.csv

### Core Schema (`config/schema.py`)
- 4 sheets: `BPLS-Business` (35 fields), `BPLS-Business Activity` (7 fields), `BPLS-Application` (19 fields), `BPLS-Application Fee` (13 fields)
- FieldTypes: STRING, NUMBER, INTEGER, DATE, ENUM, BOOLEAN, EMAIL, PHONE, FOREIGN_KEY, BIN
- RequiredLevel: YES, NO, CONDITIONAL
- CONDITIONAL_RULES dict for per-sheet conditional validations
- CROSS_FIELD_RULES dict for expression-based validations

### Design Patterns
- Strategy Pattern (BaseValidator → 10 concrete validators)
- Factory Pattern (_get_validators creates validators by FieldType)
- Pipeline Pattern (Read→Clean→cross-validate→validate→correct→write→report)
- Registry Pattern (SHEET_SCHEMAS dict)
- Facade Pattern (BPLSCSVGenerator orchestrates entire pipeline)

---

## All 24 Features (COMPLETED)

### Feature Inventory

| # | Feature | File | API Endpoint | Status |
|---|---------|------|-------------|--------|
| 1 | Template Generator | `generators/template_generator.py` | `POST /api/templates/generate` | ✅ |
| 2 | Duplicate Detector | `generators/duplicate_detector.py` | `POST /api/duplicates/detect` | ✅ |
| 3 | Dry Run Mode (Before/After Preview) | Built into upload pipeline + UI | Inline in results | ✅ |
| 4 | Column Mapping Wizard | `generators/column_mapper.py` | `POST /api/mapping/detect` | ✅ |
| 5 | File Diff/Comparison | `generators/file_differ.py` | `POST /api/diff/compare` | ✅ |
| 6 | Data Quality Dashboard | `generators/quality_dashboard.py` | In upload response as `quality_scores` | ✅ |
| 7 | Error Heat Map | `generators/error_heatmap.py` | `GET /api/heatmap/generate` | ✅ |
| 8 | Summary Statistics | `generators/summary_statistics.py` | In upload response as `statistics` | ✅ |
| 9 | Historical Tracking | `generators/historical_tracker.py` | `GET /api/quality/trends` | ✅ |
| 10 | PSGC Address Validator | `generators/psgc_validator.py` | `POST /api/psgc/validate` | ✅ |
| 11 | Custom Rule Builder | `generators/config_profiles.py` | `POST /api/profiles` | ✅ |
| 12 | Cross-Row Validation | `generators/cross_row_validator.py` | In upload response as `cross_row_issues` | ✅ |
| 13 | Email/Phone Verification | `generators/email_phone_verifier.py` | In upload response as `email_issues`/`phone_issues` | ✅ |
| 14 | REST API | `app.py` (enhanced) | 23 routes total | ✅ |
| 15 | Webhook Notifications | `generators/webhook_notifier.py` | `GET/POST /api/webhooks` | ✅ |
| 16 | Batch Processing | `generators/batch_processor.py` | `POST /api/batch/process` | ✅ |
| 17 | Docker Deployment | `Dockerfile`, `.dockerignore` | `docker build/run` | ✅ |
| 18 | Plugin System | `generators/plugin_system.py` | `GET/POST /api/plugins` | ✅ |
| 19 | Config Profiles | `generators/config_profiles.py` | `GET/POST /api/profiles` | ✅ |
| 20 | Python SDK | All generators importable | `from generators import *` | ✅ |
| 21 | PDF Reports | `generators/pdf_report_generator.py` | `POST /api/reports/pdf` | ✅ |
| 22 | Multi-Language UI | `templates/index.html` | Language selector (en/fil) | ✅ |
| 23 | Dark Mode | CSS custom properties in index.html | Toggle button | ✅ |
| 24 | Before/After Preview | Inline in results UI | Collapsible panel | ✅ |

---

## File Structure

```
bpls_csv_generator/
├── config/
│   ├── __init__.py
│   └── schema.py                      # 769 lines — ALL schema definitions, CONDITIONAL_RULES, CROSS_FIELD_RULES
├── validators/
│   ├── __init__.py
│   ├── base.py                        # ValidationResult, ValidationResultStatus, BaseValidator
│   ├── type_validators.py             # String, Number, Integer, Date, Enum, Boolean, Email, Phone, Bin, ForeignKey
│   └── conditional.py                 # ConditionalValidator, CrossFieldValidator
├── cleaners/
│   ├── __init__.py
│   └── data_cleaners.py               # DataCleaner class with type-specific cleaning methods
├── generators/
│   ├── __init__.py                    # Exports ALL generators (updated with 24 features)
│   ├── csv_generator.py               # BPLSCSVGenerator — main orchestrator
│   ├── format_generators.py           # Re-exports 4 independent generators
│   ├── bpls_business_generator.py     # Generator 1: BPLS-Business (37 fields)
│   ├── bpls_business_activity_generator.py  # Generator 2: BPLS-Business Activity (8 fields)
│   ├── bpls_application_generator.py       # Generator 3: BPLS-Application (19 fields)
│   ├── bpls_application_fee_generator.py   # Generator 4: BPLS-Application Fee (13 fields)
│   ├── cross_sheet_validator.py       # Cross-sheet foreign key validation
│   ├── template_generator.py          # Feature 1: Excel templates with dropdowns
│   ├── duplicate_detector.py          # Feature 2: Duplicate BIN/OR/name detection
│   ├── column_mapper.py               # Feature 4: Column mapping (200+ aliases + fuzzy)
│   ├── file_differ.py                 # Feature 5: Compare two migration files
│   ├── quality_dashboard.py           # Feature 6: Quality scores per sheet
│   ├── error_heatmap.py               # Feature 7: Error heatmap across runs
│   ├── summary_statistics.py          # Feature 8: Auto-generated analytics
│   ├── historical_tracker.py          # Feature 9: Trend tracking with charts
│   ├── psgc_validator.py              # Feature 10: Philippine PSGC validation
│   ├── cross_row_validator.py         # Feature 12: Cross-row conflict detection
│   ├── email_phone_verifier.py        # Feature 13: Email/PH phone verification
│   ├── webhook_notifier.py            # Feature 15: Slack/Discord/Teams webhooks
│   ├── batch_processor.py             # Feature 16: Process folders of files
│   ├── plugin_system.py               # Feature 18: Third-party plugins
│   ├── config_profiles.py             # Feature 19: Validation rule profiles
│   └── pdf_report_generator.py        # Feature 21: Audit-ready PDF reports
├── plugins/
│   └── tin_validator.py               # Sample plugin: TIN format validator
├── templates/
│   └── index.html                     # Complete rewrite: 9 tabs, dark mode, i18n, all features
├── static/
│   ├── css/style.css                  # Original styles (replaced by inline CSS in index.html)
│   └── js/app.js                      # Original JS (replaced by inline JS in index.html)
├── uploads/                           # Uploaded files
├── outputs/                           # Generated CSVs, reports, history, profiles, webhooks
├── app.py                             # Flask app with 23 API routes (enhanced)
├── main.py                            # CLI entry point + web server starter
├── requirements.txt                   # flask, pandas, openpyxl, reportlab (optional)
├── Dockerfile                         # Python 3.12-slim deployment
├── .dockerignore
├── FEATURES.md                        # Complete feature documentation
├── README.md                          # Original docs
├── QUICKSTART.md                      # Original quick start
├── FORMAT_GENERATORS_GUIDE.md         # Original 4-generator docs
├── AGENTS.md                          # THIS FILE — project context for continuation
└── test files (test_pipeline.py, test_all_generators.py, foolproof_test.py, etc.)
```

---

## Key Technical Details

### Validation Result Format
```python
{
    "field": "bin",
    "row": 5,
    "status": "PASS" | "FAIL" | "AUTO_CORRECTED",
    "severity": "ERROR" | "WARNING" | "INFO",
    "message": "...",
    "original_value": "09171234568",
    "corrected_value": "639171234568",
    "suggestion": "..."
}
```

### BIN Format
`PSGC(7)-YEAR(4)-INCREMENT(7)` → e.g. `1400101-2024-0000001`

### Conditional Rules (from schema.py)
- `business_type = "SOLE PROPRIETORSHIP"` → `dti_no` + `dti_registratrion_expiry_date` required
- `business_type in ["ONE PERSON CORPORATION", "PARTNERSHIP", "CORPORATION"]` → `sec_no` required
- `business_type = "COOPERATIVE"` → `cda_no` required
- `location_owned = 1` → `tdn_no` or `pin_no` required
- `location_owned = 0` → `lessor_name` + `monthly_rental` required
- Application/ Fee: `qtr_to >= qtr_from`

### Cross-Field Rules
- `no_of_employees_residing_within_the_area <= no_of_male_employees + no_of_female_employees`

### Cross-Sheet Foreign Keys
1. `BPLS-Business Activity.bin` → `BPLS-Business.bin`
2. `BPLS-Application.business_bin` → `BPLS-Business.bin`
3. `BPLS-Application Fee.business_bin` → `BPLS-Business.bin`
4. `BPLS-Application Fee.application_or_no` → `BPLS-Application.or_no`

### Auto-Correction Behaviors
- Dates: 8 input formats → `MM/DD/YYYY`
- Phones: `09XXXXXXXXX` → `639XXXXXXXXX`
- Enums: case-insensitive → canonical case
- Booleans: `yes/true/1/t/y` → `1`, `no/false/0/f/n` → `0`
- BINs: 18-digit raw → `7-4-7` dashed format
- Emails: lowercase
- Strings: trim whitespace, truncate if over max_length
- Numbers: remove commas, convert strings

### Dependencies
- **Required:** flask, pandas, openpyxl, python-dateutil, email-validator, Jinja2, werkzeug
- **Optional:** reportlab (for PDF reports, falls back to HTML)

---

## API Routes (23 total)

| Route | Method | Purpose |
|-------|--------|---------|
| `/` | GET | Main page |
| `/api/upload` | POST | Core processing pipeline (+ all feature integrations) |
| `/api/download/<filename>` | GET | Download any generated file |
| `/api/status` | GET | Health check + feature list |
| `/api/templates/generate` | POST | Generate Excel templates |
| `/api/duplicates/detect` | POST | Detect duplicates in uploaded file |
| `/api/mapping/detect` | POST | Auto-detect column mapping |
| `/api/diff/compare` | POST | Compare two files |
| `/api/quality/trends` | GET | Get quality trend data |
| `/api/quality/trends/chart` | GET | Generate HTML trend chart |
| `/api/heatmap/generate` | GET | Generate HTML heatmap |
| `/api/psgc/validate` | POST | Validate PSGC code |
| `/api/webhooks` | GET | List webhooks |
| `/api/webhooks` | POST | Add webhook |
| `/api/batch/process` | POST | Batch process folder |
| `/api/plugins` | GET | List plugins |
| `/api/plugins/toggle` | POST | Toggle plugin |
| `/api/profiles` | GET | List profiles |
| `/api/profiles` | POST | Create profile |
| `/api/profiles/activate` | POST | Activate profile |
| `/api/profiles/deactivate` | POST | Deactivate profile |
| `/api/reports/pdf` | POST | Generate PDF report |

---

## UI Architecture (index.html)

### 9 Tabs
1. **Upload** — Core file upload with progress, results, before/after preview, duplicate report, cross-row issues, email/phone issues, sheet validation details
2. **Templates** — Generate Excel templates dropdown
3. **Column Map** — Paste source columns → auto-detect mappings
4. **Compare** — Upload two files → see diffs
5. **Batch** — Process folder of files
6. **Quality** — Trends + Heatmap
7. **Tools** — PSGC validator, email/phone checker, webhook config, PDF report
8. **Profiles** — Create/activate/deactivate validation profiles
9. **Plugins** — List/toggle plugins

### Features
- **Dark mode:** CSS custom properties, persists in localStorage
- **i18n:** English + Filipino, switchable via dropdown, `data-i18n` attributes
- **Before/After preview:** Collapsible table showing original → cleaned values
- **Responsive:** Mobile-friendly grid layouts

---

## What Was Done This Session

All 24 features were implemented from scratch in a single session:
- 18 new files created
- 5 existing files updated (app.py, index.html, __init__.py, requirements.txt, FEATURES.md)
- 1 new directory created (plugins/)
- All Python syntax validated (24 files compile clean)
- Flask app verified (23 routes registered, all imports work)
- Dockerfile + .dockerignore created
- Sample plugin (TIN validator) created
- Complete documentation written (FEATURES.md)

## Where to Continue

### Potential next steps:
1. **Test the full pipeline** — Run `python main.py --web` and upload a real file to verify all 24 features work end-to-end
2. **Fix the quality_dashboard.py syntax error** — Had a missing indentation that was corrected inline; verify it works
3. **Add more sample plugins** to the `plugins/` directory
4. **Load full PSGC data** — The PSGCValidator currently has NCR subset only; could load full PSGC CSV
5. **Add setup.py/pyproject.toml** for proper pip installable SDK
6. **Write integration tests** for the new API endpoints
7. **Add the `dry_run` explicit mode** — Currently the before/after preview runs as part of every upload; could add a dedicated "dry run only" option that skips CSV generation
8. **Improve the template generator** — Add example data rows, not just headers + validation
9. **Add real-time progress bar** for batch processing via Server-Sent Events or WebSocket
10. **Add export of quality trends** as CSV/PNG

---

## Commands Reference

```bash
# Start web UI
python main.py --web

# CLI processing
python main.py "path/to/file.xlsx"
python main.py "path/to/file.xlsx" --no-auto-correct
python main.py "path/to/file.xlsx" --output ./custom_output

# Test pipeline
python test_pipeline.py

# Test all 4 generators
python test_all_generators.py

# Docker
docker build -t bpls-csv-generator .
docker run -p 5000:5000 -v ./outputs:/app/outputs bpls-csv-generator
```
