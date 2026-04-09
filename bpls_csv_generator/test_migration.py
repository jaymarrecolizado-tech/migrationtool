"""
Quick test with the actual migration rules Excel file
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from generators.csv_generator import BPLSCSVGenerator

# Test with actual migration rules file
input_file = r"C:\Users\DICT\Desktop\RULES\migration rules.xlsx"
output_dir = r"C:\Users\DICT\Desktop\RULES\bpls_csv_generator\migration_outputs"

if not os.path.exists(input_file):
    print(f"❌ Input file not found: {input_file}")
    sys.exit(1)

print("="*70)
print("🚀 Processing Migration Rules Excel File")
print("="*70)
print()

generator = BPLSCSVGenerator(output_dir)
summary = generator.process_excel_file(input_file, auto_correct=True)

print()
print("="*70)
print("✅ PROCESSING COMPLETE!")
print("="*70)
print(f"📊 Total rows processed: {summary['total_rows']}")
print(f"📑 Sheets processed: {len(summary['sheets_processed'])}")
print(f"❌ Errors found: {summary['total_errors']}")
print(f"⚠️  Warnings: {summary['total_warnings']}")
print(f"🔧 Auto-corrections: {summary['total_corrections']}")
print(f"\n📁 Output files saved to: {os.path.abspath(output_dir)}")
print("="*70)
