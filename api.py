from dotenv import load_dotenv

load_dotenv()

import sys

# Windows consoles often default to cp1252; force UTF-8 so Hindi/Unicode in logs
# and transcripts does not crash background jobs.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import threading
import uuid
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from core.rag_engine import ask_question
from main import run_pipeline

app = FastAPI(title="VidMind API")

UPLOAD_DIR = Path("downloads/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

sessions: dict[str, dict] = {}
jobs: dict[str, dict] = {}


def _run_job(job_id: str, source: str, language: str) -> None:
    try:
        jobs[job_id]["status"] = "processing"
        jobs[job_id]["stage"] = "Downloading / loading audio..."
        result = run_pipeline(source, language)
        session_id = str(uuid.uuid4())
        sessions[session_id] = {"rag_chain": result.pop("rag_chain")}
        jobs[job_id].update(
            {
                "status": "done",
                "stage": "Complete",
                "session_id": session_id,
                "result": result,
            }
        )
    except Exception as exc:
        jobs[job_id].update(
            {
                "status": "error",
                "stage": "Failed",
                "error": str(exc),
            }
        )


@app.post("/api/analyze")
async def analyze(
    language: str = Form("english"),
    source: str = Form(""),
    file: Optional[UploadFile] = File(None),
):
    if file and file.filename:
        file_path = UPLOAD_DIR / f"{uuid.uuid4()}_{file.filename}"
        file_path.write_bytes(await file.read())
        source_path = str(file_path)
    elif source.strip():
        source_path = source.strip()
    else:
        raise HTTPException(status_code=400, detail="Provide a YouTube URL or upload a file.")

    job_id = str(uuid.uuid4())
    jobs[job_id] = {"status": "queued", "stage": "Starting..."}
    thread = threading.Thread(
        target=_run_job,
        args=(job_id, source_path, language),
        daemon=True,
    )
    thread.start()
    return {"job_id": job_id}


@app.get("/api/jobs/{job_id}")
def get_job(job_id: str):
    if job_id not in jobs:
        raise HTTPException(
            status_code=404,
            detail="Job not found. The server may have restarted — please analyze again.",
        )

    job = jobs[job_id]
    response = {"status": job["status"], "stage": job.get("stage", "")}

    if job["status"] == "done":
        response["session_id"] = job["session_id"]
        response["result"] = job["result"]
    elif job["status"] == "error":
        response["error"] = job.get("error", "Unknown error.")

    return response


class ChatRequest(BaseModel):
    session_id: str
    question: str


@app.post("/api/chat")
def chat(req: ChatRequest):
    session = sessions.get(req.session_id)
    if not session:
        raise HTTPException(
            status_code=404,
            detail="Session expired. Please analyze a video again.",
        )

    try:
        answer = ask_question(session["rag_chain"], req.question.strip())
        return {"answer": answer}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.delete("/api/sessions/{session_id}")
def clear_session(session_id: str):
    sessions.pop(session_id, None)
    return {"ok": True}


app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
def root():
    return FileResponse("static/index.html")
