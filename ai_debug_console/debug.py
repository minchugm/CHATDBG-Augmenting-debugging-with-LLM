# ai_debug_console/debug.py
import datetime, os, sys, tempfile, json
from urllib import request
from .config import get_api_key, get_model_name, get_provider, get_openrouter_api_key, get_openrouter_base_url
from .utils import ensure_utf8_io
from .project import run_project
from typing import Callable

ensure_utf8_io()

# Try to import google.generativeai but be robust
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except Exception:
    genai = None
    GEMINI_AVAILABLE = False

def init_model():
    provider = get_provider()
    if provider == "openrouter":
        api_key = get_openrouter_api_key()
        model_name = get_model_name()
        base = get_openrouter_base_url()
        if not api_key:
            return None
        def _query(prompt: str):
            url = f"{base}/chat/completions"
            body = {
                "model": model_name,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0
            }
            data = json.dumps(body).encode("utf-8")
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            }
            req = request.Request(url, data=data, headers=headers, method="POST")
            try:
                with request.urlopen(req, timeout=60) as resp:
                    out = resp.read().decode("utf-8")
                    j = json.loads(out)
                c = j.get("choices", [])
                if c:
                    m = c[0].get("message", {})
                    return m.get("content", out)
                return out
            except Exception as e:
                return f"[MODEL ERROR] {e}"
        return _query
    api_key = get_api_key()
    model_name = get_model_name()
    if not api_key or not GEMINI_AVAILABLE:
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

def delta_minimize(inp_path: str, run_single_file_fn: Callable, run_target: str):
    orig = open(inp_path, "rb").read()
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
        try:
            os.unlink(tmp_path)
        except Exception:
            pass
        if se:
            best = candidate
            hi = mid
        else:
            lo = mid
        rounds += 1
    with tempfile.NamedTemporaryFile(delete=False) as tf2:
        tf2.write(best)
        minimized_path = tf2.name
    return len(orig), len(best), minimized_path

def safe_query_model(model, prompt: str):
    if model is None:
        return ("[OFFLINE] No model available. Configure provider and API key (Gemini, Groq, or OpenRouter).")
    try:
        if callable(model):
            return model(prompt)
        resp = model.generate_content(prompt)
        if hasattr(resp, "text"):
            return resp.text
        if hasattr(resp, "candidates") and resp.candidates:
            return resp.candidates[0].text
        return str(resp)
    except Exception as e:
        return f"[MODEL ERROR] {e}"

def start_debug_loop(model, all_sources: str, run_single_file_fn: Callable, run_target: str, project_mode=False):
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
    print("❓ ChatDBG > Entering debug mode. Type 'exit' to quit.\n")
    while True:
        q = input("❓ ChatDBG  > ").strip()
        if not q:
            continue
        if q.lower() in ("exit", "quit"):
            print("👋 Exiting debug mode.")
            break
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
        prompt = f"{context}\n\nUser Question: {q}\n\nAnswer strictly about THIS program/project (use the code, stdout, stderr above)."
        answer = safe_query_model(model, prompt)
        print("\n🛠️ Result:\n")
        print(answer)
