"""
BPLS CSV Generator - Main Entry Point
Can be run as CLI or Web server
"""

import argparse
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))


def main():
    parser = argparse.ArgumentParser(
        description="BPLS CSV Format Generator - Validate and transform migration data"
    )
    parser.add_argument(
        "input",
        nargs="?",
        help="Path to Excel file to process"
    )
    parser.add_argument(
        "--output", "-o",
        default="outputs",
        help="Output directory (default: outputs)"
    )
    parser.add_argument(
        "--web", "-w",
        action="store_true",
        help="Start web interface instead of processing file"
    )
    parser.add_argument(
        "--no-auto-correct",
        action="store_true",
        help="Disable auto-correction of data issues"
    )
    parser.add_argument(
        "--port", "-p",
        type=int,
        default=5000,
        help="Port for web interface (default: 5000)"
    )

    args = parser.parse_args()

    if args.web:
        # Start web interface
        print("🚀 Starting BPLS CSV Generator Web Interface...")
        print(f"📍 Open http://localhost:{args.port} in your browser")
        print("\nPress Ctrl+C to stop")

        from app import app
        app.config["OUTPUT_FOLDER"] = os.path.abspath(args.output)
        app.run(debug=True, host="0.0.0.0", port=args.port)

    elif args.input:
        # Process file directly
        from generators.csv_generator import BPLSCSVGenerator

        input_file = os.path.abspath(args.input)

        if not os.path.exists(input_file):
            print(f"❌ Error: File not found: {input_file}")
            sys.exit(1)

        # Detect file type
        file_ext = input_file.rsplit(".", 1)[1].lower()
        if file_ext not in ("xlsx", "xls", "csv"):
            print(f"❌ Error: Unsupported file type .{file_ext}. Please use .xlsx, .xls, or .csv")
            sys.exit(1)

        print(f"📖 Processing: {input_file}")
        print(f"📂 Output directory: {args.output}")
        print(f"⚡ Auto-correct: {'OFF' if args.no_auto_correct else 'ON'}")
        print()

        generator = BPLSCSVGenerator(args.output)

        if file_ext == "csv":
            summary = generator.process_csv_file(
                input_file,
                auto_correct=not args.no_auto_correct
            )
        else:
            summary = generator.process_excel_file(
                input_file,
                auto_correct=not args.no_auto_correct
            )

        print("\n" + "="*60)
        print("✅ PROCESSING COMPLETE!")
        print("="*60)
        print(f"📊 Total rows processed: {summary['total_rows']}")
        print(f"📑 Sheets processed: {len(summary['sheets_processed'])}")
        print(f"❌ Errors found: {summary['total_errors']}")
        print(f"⚠️  Warnings: {summary['total_warnings']}")
        print(f"🔧 Auto-corrections: {summary['total_corrections']}")
        print(f"\n📁 Output files saved to: {os.path.abspath(args.output)}")
        print("="*60)

    else:
        parser.print_help()
        print("\n💡 Examples:")
        print("  Process an Excel file:")
        print("    python main.py 'migration rules.xlsx'")
        print("  Process a CSV file:")
        print("    python main.py 'BPLS-Business.csv'")
        print("\n  Start web interface:")
        print("    python main.py --web")
        print("\n  Process without auto-correction:")
        print("    python main.py 'migration rules.xlsx' --no-auto-correct")


if __name__ == "__main__":
    main()
