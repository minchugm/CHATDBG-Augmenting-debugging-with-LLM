#!/usr/bin/env python3
import argparse, sys, io, datetime
from config import get_gemini_model
from runner import run_single_file
from project import collect_project_files
from debug import start_debug_loop

# Fix Unicode errors
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

parser = argparse.ArgumentParser(description="AI Debug Console")
subparsers = parser.add_subparsers(dest="command")
sp_debug = subparsers.add_parser("debug", help="Run & debug source code")
sp_debug.add_argument("--file", help="Path to a single source file")
sp_debug.add_argument("--project", help="Path to a project folder")

args = parser.parse_args()

if args.command == "debug":
    model = get_gemini_model()
    if not model:
        exit(1)

    all_sources, run_output, error_message, run_target = "", "", "", None

    if args.file:
        run_target = args.file
        with open(args.file, "r", encoding="utf-8") as f:
            all_sources = f.read()
        run_output, error_message = run_single_file(args.file)

    elif args.project:
        all_sources, source_files = collect_project_files(args.project)
        if not source_files:
            print("⚠️ No supported source files found in project.")
            exit(1)
        run_target = source_files[0]
        run_output, error_message = run_single_file(run_target)

    else:
        print("⚠️ Please provide --file or --project")
        exit(1)

    if not error_message:
        print("✅ Program executed successfully!\n")
        print(run_output)
        exit(0)

    context = f"""
Timestamp: {datetime.datetime.utcnow().isoformat()}Z

Source Code:
{all_sources}

Output:
{run_output}

Errors:
{error_message}
"""
    start_debug_loop(model, context, run_single_file, run_target)
