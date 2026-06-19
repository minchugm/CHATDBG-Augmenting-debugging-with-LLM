# ai_debug_console/debug.py
import datetime, os, sys
from .config import get_api_key, get_model_name
from .utils import ensure_utf8_io
from .project import run_project
from typing import Callable, List, Tuple
import re
import pathlib
import tempfile

ensure_utf8_io()

# Try to import google.generativeai but be robust
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except Exception:
    genai = None
    GEMINI_AVAILABLE = False

def init_model():
    api_key = get_api_key()
    model_name = get_model_name()
    if not api_key or not GEMINI_AVAILABLE:
        # fallback mode
        return None
    genai.configure(api_key=api_key)
    return genai.GenerativeModel(model_name)

def build_context(all_sources: str, stdout: str, stderr: str) -> str:
    return f"""
Timestamp: {datetime.datetime.utcnow().isoformat()}Z

SOURCE CODE:
{all_sources}

STDOUT:
{stdout}

STDERR:
{stderr}
"""

def safe_query_model(model, prompt: str):
    if model is None:
        # offline stub response
        return ("[OFFLINE] No model available. Install `google-generativeai` and set GOOGLE_API_KEY in env or config.json.\n"
                "You can still ask: 'what is the error' and the tool will attempt to analyze stderr/stdout locally.")
    try:
        resp = model.generate_content(prompt)
        # Some wrappers return .text or .candidates — fallbacks:
        if hasattr(resp, "text"):
            return resp.text
        if hasattr(resp, "candidates") and resp.candidates:
            return resp.candidates[0].text
        return str(resp)
    except Exception as e:
        return f"[MODEL ERROR] {e}"

def _extract_frames(stderr: str) -> List[Tuple[str, int, str]]:
    frames = []
    py = re.findall(r"File\s+\"(.+?)\",\s+line\s+(\d+),\s+in\s+([\w_<>]+)", stderr)
    for f, ln, fn in py:
        try:
            frames.append((f, int(ln), fn))
        except Exception:
            pass
    js = re.findall(r"at\s+(?:[\w$.<>]+)?\s*\((.+?):(\d+)(?::\d+)?\)", stderr)
    for f, ln in js:
        try:
            frames.append((f, int(ln), ""))
        except Exception:
            pass
    java = re.findall(r"\(([^:]+\.java):(\d+)\)", stderr)
    for f, ln in java:
        try:
            frames.append((f, int(ln), ""))
        except Exception:
            pass
    direct = re.findall(r"([A-Za-z]:\\[^\n:]+):(\d+):", stderr)
    for f, ln in direct:
        try:
            frames.append((f, int(ln), ""))
        except Exception:
            pass
    return frames

def _rank_and_format(frames: List[Tuple[str,int,str]], run_target: str, top_n: int = 5) -> str:
    base = pathlib.Path(run_target).parent if run_target else None
    scored = []
    for f, ln, fn in frames:
        p = pathlib.Path(f)
        score = 0
        try:
            if base and p.resolve().as_posix().startswith(base.resolve().as_posix()):
                score += 5
        except Exception:
            pass
        s = p.as_posix().lower()
        if any(x in s for x in ["node_modules", "site-packages", "\.m2", "jdk", "java/lib"]):
            score -= 3
        scored.append((score, f, ln, fn))
    scored.sort(key=lambda x: (-x[0], x[1], x[2]))
    out_lines = []
    for score, f, ln, fn in scored[:top_n]:
        snippet = ""
        try:
            with open(f, "r", encoding="utf-8", errors="ignore") as fh:
                lines = fh.readlines()
            idx = max(0, ln-2)
            seg = lines[idx:ln+1]
            snippet = "".join(seg)
        except Exception:
            snippet = ""
        out_lines.append(f"{f}:{ln} | {fn}\n{snippet}")
    return "\n".join(out_lines) or ""

def start_debug_loop(model, all_sources: str, run_single_file_fn: Callable, run_target: str, project_mode=False, enable_localization=True, plain_output=False):
    """
    Interactive debug loop.
    run_single_file_fn: function(path)->(stdout, stderr)
    run_target: file path or project path
    project_mode: if True, uses run_project to stream logs (via project.run_project)
    """
    print("❌ Program has errors. Entering debug mode...\n")
    stdout, stderr = "", ""
    if project_mode:
        # stream run_project logs (non-blocking)
        def log_cb(line):
            print("[PROJECT LOG]", line)
        # run_project will return (stdout, stderr)
        res = run_project(run_target, log_cb)
        if isinstance(res, tuple):
            stdout, stderr = res
        else:
            stdout, stderr = "", str(res)
    else:
        stdout, stderr = run_single_file_fn(run_target)

    context = build_context(all_sources, stdout, stderr)
    suspects_block = ""
    if enable_localization and stderr:
        frames = _extract_frames(stderr)
        suspects_block = _rank_and_format(frames, run_target)
    print("❓ ChatDBG > Entering debug mode. Type 'exit' to quit.\n")
    while True:
        q = input("❓ ChatDBG  > ").strip()
        if not q:
            continue
        if q.lower() in ("exit", "quit"):
            print("👋 Exiting debug mode.")
            break
        if q.lower().startswith("minimize "):
            path_arg = q.split(None, 1)[1]
            try:
                orig = open(path_arg, "rb").read()
            except Exception as e:
                print(f"❌ Cannot read input file: {e}")
                continue
            cur = orig
            lo, hi = 0, len(cur)
            best = cur
            rounds = 0
            while hi - lo > 1 and rounds < 10:
                mid = (lo + hi) // 2
                candidate = cur[:mid]
                with tempfile.NamedTemporaryFile(delete=False) as tf:
                    tf.write(candidate)
                    tmp_path = tf.name
                os.environ['AI_DEBUG_INPUT_FILE'] = tmp_path
                so, se = run_single_file_fn(run_target)
                os.unlink(tmp_path)
                if se:
                    best = candidate
                    hi = mid
                else:
                    lo = mid
                rounds += 1
            with tempfile.NamedTemporaryFile(delete=False) as tf2:
                tf2.write(best)
                minimized_path = tf2.name
            print(f"🔎 Delta result: {len(orig)} → {len(best)} bytes. Path: {minimized_path}")
            continue
        if q.lower() == "rerun":
            print("🔁 Re-running...\n")
            if project_mode:
                # re-run project
                def cb(line): print("[PROJECT LOG]", line)
                res = run_project(run_target, cb)
                if isinstance(res, tuple):
                    stdout, stderr = res
                else:
                    stdout, stderr = "", str(res)
            else:
                stdout, stderr = run_single_file_fn(run_target)
            if not stderr:
                print("✅ Program executed successfully!\n")
                print(stdout)
            else:
                print("❌ Still errors.\n")
                print("STDOUT:\n", stdout)
                print("STDERR:\n", stderr)
            continue

        # otherwise ask model (or fallback)
        extra = f"\n\nSuspected Locations:\n{suspects_block}\n" if suspects_block else "\n"
        prompt = f"{context}{extra}\nUser Question: {q}\n\nAnswer strictly about THIS program/project (use the code, stdout, stderr above)."
        answer = safe_query_model(model, prompt)
        supports_ansi = (
            sys.stdout.isatty() or
            os.getenv('WT_SESSION') or
            os.getenv('ANSICON') or
            os.getenv('ConEmuANSI') == 'ON'
        )
        no_style_env = os.getenv('AI_DEBUG_NO_STYLE') == '1'
        use_style = supports_ansi and not no_style_env and not plain_output
        if use_style:
            BLACK = "\u001B[30m"; BG_WHITE = "\u001B[47m"; RESET = "\u001B[0m"
            print("\n" + BG_WHITE + BLACK + "🛠️ Result:" + RESET + "\n")
            print(BG_WHITE + BLACK + answer + RESET)
        else:
            print("\n🛠️ Result:\n")
            print(answer)
