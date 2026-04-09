"""
Test All 4 Format Generators Independently
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from generators.format_generators import (
    BPLSBusinessFormatGenerator,
    BPLSBusinessActivityFormatGenerator,
    BPLSApplicationFormatGenerator,
    BPLSApplicationFeeFormatGenerator,
)

# Input and output paths
input_file = r"C:\Users\DICT\Desktop\RULES\migration rules.xlsx"
output_dir = r"C:\Users\DICT\Desktop\RULES\bpls_csv_generator\test_outputs"

if not os.path.exists(input_file):
    print(f"❌ Input file not found: {input_file}")
    sys.exit(1)

print("="*70)
print("🧪 Testing All 4 BPLS Format Generators")
print("="*70)

# ============================================================
# Test 1: BPLS-Business Format Generator
# ============================================================
print("\n\n")
print("="*70)
print("TEST 1: BPLS-Business Format Generator")
print("="*70)

generator1 = BPLSBusinessFormatGenerator(output_dir)
summary1 = generator1.process(input_file, auto_correct=True)

# ============================================================
# Test 2: BPLS-Business Activity Format Generator
# ============================================================
print("\n\n")
print("="*70)
print("TEST 2: BPLS-Business Activity Format Generator")
print("="*70)

generator2 = BPLSBusinessActivityFormatGenerator(output_dir)
summary2 = generator2.process(input_file, auto_correct=True)

# ============================================================
# Test 3: BPLS-Application Format Generator
# ============================================================
print("\n\n")
print("="*70)
print("TEST 3: BPLS-Application Format Generator")
print("="*70)

generator3 = BPLSApplicationFormatGenerator(output_dir)
summary3 = generator3.process(input_file, auto_correct=True)

# ============================================================
# Test 4: BPLS-Application Fee Format Generator
# ============================================================
print("\n\n")
print("="*70)
print("TEST 4: BPLS-Application Fee Format Generator")
print("="*70)

generator4 = BPLSApplicationFeeFormatGenerator(output_dir)
summary4 = generator4.process(input_file, auto_correct=True)

# ============================================================
# Final Summary
# ============================================================
print("\n\n")
print("="*70)
print("✅ ALL 4 FORMAT GENERATORS TESTED SUCCESSFULLY!")
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

print("📁 Generated Files:")
print("-" * 70)

for s in summaries:
    print(f"  ✓ {s['sheet']}: {s['output_file']}")
    print(f"    - {s['total_rows']} rows, {s['total_errors']} errors, {s['total_corrections']} corrections")

print()
print("="*70)
print("💡 Output files are in:")
print(f"   {os.path.abspath(output_dir)}")
print("="*70)
