import csv
import io
import os
import secrets
from pathlib import Path

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.responses import FileResponse, Response
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel

import db
import search
import triage

load_dotenv()

app = FastAPI(title="SupportOps Copilot", docs_url=None, redoc_url=None, openapi_url=None)
basic = HTTPBasic()
db.init_db()

MIN_LEN, MAX_LEN = 10, 3000


class TicketIn(BaseModel):
    text: str


def require_login(credentials: HTTPBasicCredentials = Depends(basic)):
    user = os.getenv("APP_USER", "")
    password = os.getenv("APP_PASSWORD", "")
    ok_user = secrets.compare_digest(credentials.username.encode(), user.encode())
    ok_pass = secrets.compare_digest(credentials.password.encode(), password.encode())
    if not (user and password and ok_user and ok_pass):
        raise HTTPException(
            status_code=401,
            detail="Wrong username or password",
            headers={"WWW-Authenticate": "Basic"},
        )


def require_token(x_webhook_token: str = Header(default="")):
    token = os.getenv("WEBHOOK_TOKEN", "")
    if not token:
        raise HTTPException(status_code=503, detail="WEBHOOK_TOKEN is not set on the server")
    if not secrets.compare_digest(x_webhook_token.encode(), token.encode()):
        raise HTTPException(status_code=401, detail="Wrong token")


def handle(text, source):
    text = text.strip()
    if len(text) < MIN_LEN or len(text) > MAX_LEN:
        raise HTTPException(
            status_code=400,
            detail=f"Ticket must be {MIN_LEN} to {MAX_LEN} characters",
        )
    result = triage.triage(text)
    result["id"] = db.save_ticket(text, result, source=source)
    return result


@app.get("/")
def home(_=Depends(require_login)):
    page = Path(__file__).parent / "index.html"
    if page.exists():
        return FileResponse(page)
    return {"message": "SupportOps Copilot API is running. The web page comes in Step 8."}


@app.get("/status")
def status(_=Depends(require_login)):
    return {"mode": "mock" if search.is_mock() else "gemini"}


@app.post("/tickets")
def create_ticket(ticket: TicketIn, _=Depends(require_login)):
    return handle(ticket.text, "web")


@app.post("/webhook/ticket", status_code=201)
def webhook_ticket(ticket: TicketIn, _=Depends(require_token)):
    return handle(ticket.text, "webhook")


@app.get("/tickets")
def tickets(_=Depends(require_login)):
    return db.list_tickets()


@app.get("/stats")
def stats(_=Depends(require_login)):
    return db.get_stats()


@app.get("/export.csv")
def export_csv(_=Depends(require_login)):
    rows = db.list_tickets(limit=10000)
    out = io.StringIO()
    if rows:
        writer = csv.DictWriter(out, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    return Response(
        content=out.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=tickets.csv"},
    )