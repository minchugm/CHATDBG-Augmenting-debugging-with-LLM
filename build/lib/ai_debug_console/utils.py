# ai_debug_console/utils.py
import sys, io, shutil

def ensure_utf8_io():
    """
    Wrap stdout/stderr to use UTF-8 on Windows.
    Call early (CLI) to avoid UnicodeEncodeError.
    """
    try:
        if sys.stdout.encoding.lower() != "utf-8":
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    except Exception:
        pass
    try:
        if sys.stderr.encoding.lower() != "utf-8":
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
    except Exception:
        pass

def which(cmd):
    """Return path to executable or None"""
    return shutil.which(cmd)
