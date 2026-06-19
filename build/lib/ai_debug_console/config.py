# ai_debug_console/config.py
import json
import os

CONFIG_FILE = os.path.join(os.path.dirname(__file__), "..", "config.json")

def load_config():
    try:
        path = os.path.abspath(CONFIG_FILE)
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {}

def get_api_key():
    # 1) prefer env var GOOGLE_API_KEY
    env = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
    if env:
        return env
    cfg = load_config()
    return cfg.get("google_api_key")

def get_provider():
    cfg = load_config()
    return cfg.get("provider", "gemini")

def get_groq_api_key():
    env = os.environ.get("GROQ_API_KEY")
    if env:
        return env
    cfg = load_config()
    return cfg.get("groq_api_key")

def get_openrouter_api_key():
    env = os.environ.get("OPENROUTER_API_KEY")
    if env:
        return env
    cfg = load_config()
    return cfg.get("openrouter_api_key")

def get_openrouter_base_url():
    cfg = load_config()
    return cfg.get("openrouter_base_url", "https://openrouter.ai/api/v1")

def get_model_name():
    cfg = load_config()
    return cfg.get("model", "gemini-2.5-flash")
