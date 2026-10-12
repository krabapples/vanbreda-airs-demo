from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI  # noqa: E402
from fastapi.responses import FileResponse  # noqa: E402
from fastapi.staticfiles import StaticFiles  # noqa: E402
from pydantic import BaseModel  # noqa: E402

from . import agent  # noqa: E402

app = FastAPI(title="Vanbreda AIRS Demo Agent")
STATIC = Path(__file__).parent / "static"


class ChatRequest(BaseModel):
    messages: list[dict]


@app.post("/api/chat")
async def chat(req: ChatRequest):
    history = [m for m in req.messages if m.get("role") in ("user", "assistant")]
    return await agent.run_agent(history)


@app.get("/api/health")
async def health():
    return {"ok": True, "endpoint_configured": bool(agent.ENDPOINT), "model": agent.MODEL}


app.mount("/static", StaticFiles(directory=STATIC), name="static")


@app.get("/")
async def index():
    return FileResponse(STATIC / "index.html")
