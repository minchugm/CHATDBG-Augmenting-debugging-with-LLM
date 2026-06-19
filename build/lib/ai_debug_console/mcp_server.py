# ai_debug_console/mcp_server.py
"""
Minimal MCP server stub for your local MCP integration.
This is a tiny FastAPI server that can receive debug messages or send model responses.
Install fastapi + uvicorn to run it: pip install fastapi uvicorn
Run: uvicorn ai_debug_console.mcp_server:app --port 8765 --reload
"""
from fastapi import FastAPI
from pydantic import BaseModel
import asyncio

app = FastAPI()

class Message(BaseModel):
    project: str
    level: str
    text: str

@app.post("/mcp/log")
async def mcp_log(msg: Message):
    print(f"[MCP LOG] [{msg.project}] [{msg.level}] {msg.text}")
    return {"ok": True}

@app.get("/mcp/ping")
async def ping():
    return {"status": "alive"}
