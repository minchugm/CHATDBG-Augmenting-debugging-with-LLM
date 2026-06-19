from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Any, Dict
from .config import get_gemini_model, load_config
import uvicorn
import json

app = FastAPI(title="AI Debug MCP Server")

class AnalyzeRequest(BaseModel):
    question: str
    context: Dict[str, Any]

@app.post("/analyze")
def analyze(req: AnalyzeRequest):
    """
    Receives question + context, calls Gemini via config.get_gemini_model(),
    and returns {"answer": "..."}.
    """
    try:
        model = get_gemini_model()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Config error: {e}")

    # Build a saner prompt
    sources = req.context.get("sources", "")
    run_target = req.context.get("run_target", "")
    prompt = f"""
You are an AI debugger. Use ONLY the code and errors in 'sources' and the run target to answer.
RUN TARGET: {run_target}

SOURCES:
{sources[:15000]}

USER QUESTION:
{req.question}

Provide a practical answer focused on the program/project only. If asked to provide corrected code, return only the full corrected file contents in code block markdown.
"""
    try:
        resp = model.generate_content(prompt)
        answer_text = getattr(resp, "text", str(resp))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Model error: {e}")

    return {"answer": answer_text}

# Optional: start with `python -m ai_debug_console.server` if you add __main__ below.
if __name__ == "__main__":
    uvicorn.run("ai_debug_console.server:app", host="127.0.0.1", port=9009, reload=True)
