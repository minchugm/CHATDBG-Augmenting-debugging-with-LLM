# ai_debug_console/cli.py
#!/usr/bin/env python3
import argparse
import os
import sys
from .config import get_api_key
from .utils import ensure_utf8_io
from .runner import run_single_file
from .project import collect_project_files, run_project
from .debug import init_model, start_debug_loop, delta_minimize

ensure_utf8_io()

def main(argv=None):
    parser = argparse.ArgumentParser(prog="ai-debug", description="AI Debug Console")
    sub = parser.add_subparsers(dest="command")
    sp_debug = sub.add_parser("debug", help="Run & debug")
    sp_debug.add_argument("--file", help="Single file path")
    sp_debug.add_argument("--project", help="Project folder path")
    sp_debug.add_argument("--offline", action="store_true", help="Do not call remote model (fallback)")
    sp_debug.add_argument("--no-localize", action="store_true", help="Disable suspected error location hints")
    sp_debug.add_argument("--no-style", action="store_true", help="Disable colored/boxed output")
    sp_debug.add_argument("--minimize", help="Input file path to minimize (single-file mode)")

    args = parser.parse_args(argv)

    if args.command != "debug":
        parser.print_help()
        return 1

    model = init_model() if not args.offline else None

    if args.file:
        target = os.path.abspath(args.file)
        if not os.path.exists(target):
            print(f"⚠️ File not found: {target}")
            return 1
        if args.minimize:
            inp = os.path.abspath(args.minimize)
            if not os.path.exists(inp):
                print(f"⚠️ Input file not found: {inp}")
                return 1
            try:
                orig_len, best_len, minimized_path = delta_minimize(inp, run_single_file, target)
            except Exception as e:
                print(f"❌ Delta minimize failed: {e}")
                return 1
            print(f"🔎 Delta result: {orig_len} → {best_len} bytes. Path: {minimized_path}")
            os.environ['AI_DEBUG_INPUT_FILE'] = minimized_path
            stdout, stderr = run_single_file(target)
            if stderr:
                print("❌ Program errors persist with minimized input.\n")
                print("STDERR:\n", stderr)
                with open(target, "r", encoding="utf-8", errors="ignore") as f:
                    src = f.read()
                try:
                    start_debug_loop(model, src, run_single_file, target, project_mode=False, enable_localization=(not args.no_localize), plain_output=args.no_style)
                except TypeError:
                    start_debug_loop(model, src, run_single_file, target, project_mode=False)
            else:
                print("✅ Program executes with minimized input.\n")
                print(stdout)
            return 0
        stdout, stderr = run_single_file(target)
        if not stderr:
            print("✅ Program executed successfully!\n")
            print(stdout)
            # only enter debug mode on explicit ask via CLI or if errors
            return 0
        # else enter debug loop
        with open(target, "r", encoding="utf-8", errors="ignore") as f:
            src = f.read()
        try:
            start_debug_loop(model, src, run_single_file, target, project_mode=False, enable_localization=(not args.no_localize))
        except TypeError:
            start_debug_loop(model, src, run_single_file, target, project_mode=False)
        return 0

    if args.project:
        project = os.path.abspath(args.project)
        if not os.path.isdir(project):
            print("⚠️ Project folder not found.")
            return 1
        all_sources, files = collect_project_files(project)
        if not files:
            print("⚠️ No supported source files found in project.")
            return 1
        if args.minimize:
            inp = os.path.abspath(args.minimize)
            if not os.path.exists(inp):
                print(f"⚠️ Input file not found: {inp}")
                return 1
            try:
                def _run_once(_ignored):
                    return run_project(project, lambda _line: None)
                orig_len, best_len, minimized_path = delta_minimize(inp, _run_once, project)
            except Exception as e:
                print(f"❌ Delta minimize failed: {e}")
                return 1
            print(f"🔎 Delta result: {orig_len} → {best_len} bytes. Path: {minimized_path}")
            os.environ['AI_DEBUG_INPUT_FILE'] = minimized_path
        def cb(line):
            print("[PROJECT LOG]", line)
        stdout, stderr = run_project(project, cb)
        if not stderr:
            print("✅ Project executed successfully!\n")
            print(stdout)
            return 0
        try:
            start_debug_loop(model, all_sources, run_single_file, project, project_mode=True, enable_localization=(not args.no_localize), plain_output=args.no_style)
        except TypeError:
            start_debug_loop(model, all_sources, run_single_file, project, project_mode=True)
        return 0

    print("⚠️ Provide --file <file> or --project <folder>")
    return 1

if __name__ == "__main__":
    sys.exit(main())
