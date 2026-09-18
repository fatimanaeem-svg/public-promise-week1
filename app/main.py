import io
import os
import secrets
import uuid

import qrcode
from fastapi import Depends, FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse, StreamingResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.status import HTTP_401_UNAUTHORIZED

from . import config, db
from .rate_limit import is_rate_limited
from .ws_manager import manager

app = FastAPI(title=config.EVENT_TITLE)

BASE_DIR = os.path.dirname(__file__)
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")

security = HTTPBasic()

DEVICE_COOKIE = "ppw_device"


@app.on_event("startup")
def on_startup() -> None:
    db.init_db()


def _check_admin(credentials: HTTPBasicCredentials) -> None:
    valid_user = secrets.compare_digest(credentials.username, config.ADMIN_USERNAME)
    valid_pass = secrets.compare_digest(credentials.password, config.ADMIN_PASSWORD)
    if not (valid_user and valid_pass):
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


@app.get("/", response_class=HTMLResponse)
def submit_page(request: Request):
    response = templates.TemplateResponse(
        "submit.html",
        {
            "request": request,
            "event_title": config.EVENT_TITLE,
            "question_text": config.QUESTION_TEXT,
        },
    )
    if not request.cookies.get(DEVICE_COOKIE):
        device_token = str(uuid.uuid4())
        response.set_cookie(
            DEVICE_COOKIE, device_token, max_age=60 * 60 * 24 * 30, httponly=True, samesite="lax"
        )
    return response


@app.post("/api/submit")
async def submit(request: Request):
    ip = _client_ip(request)
    if is_rate_limited(ip):
        return JSONResponse({"ok": False, "error": "Too many requests. Please slow down."}, status_code=429)

    body = await request.json()
    name = str(body.get("name", "")).strip()
    answer = str(body.get("answer", "")).strip()

    if not name or not answer:
        return JSONResponse({"ok": False, "error": "Name and answer are both required."}, status_code=400)
    if len(name) > config.MAX_NAME_LENGTH:
        name = name[: config.MAX_NAME_LENGTH]
    if len(answer) > config.MAX_ANSWER_LENGTH:
        answer = answer[: config.MAX_ANSWER_LENGTH]

    device_token = request.cookies.get(DEVICE_COOKIE) or str(uuid.uuid4())

    if db.has_submitted(device_token):
        return JSONResponse({"ok": False, "duplicate": True, "error": "You've already submitted."}, status_code=200)

    submission = db.insert_submission(name=name, answer=answer, device_token=device_token, ip=ip)
    await manager.broadcast_submission(
        {"id": submission["id"], "name": submission["name"], "answer": submission["answer"]}
    )

    resp = JSONResponse({"ok": True})
    resp.set_cookie(DEVICE_COOKIE, device_token, max_age=60 * 60 * 24 * 30, httponly=True, samesite="lax")
    return resp


@app.get("/display", response_class=HTMLResponse)
def display_page(request: Request):
    return templates.TemplateResponse(
        "display.html",
        {
            "request": request,
            "event_title": config.EVENT_TITLE,
            "question_text": config.QUESTION_TEXT,
        },
    )


@app.get("/api/recent")
def api_recent(limit: int = 20):
    return db.get_recent_submissions(limit=limit)


@app.websocket("/ws/display")
async def ws_display(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception:
        manager.disconnect(websocket)


@app.get("/qr", response_class=HTMLResponse)
def qr_page(request: Request):
    submit_url = str(request.base_url)
    return templates.TemplateResponse(
        "qr.html",
        {"request": request, "event_title": config.EVENT_TITLE, "submit_url": submit_url},
    )


@app.get("/qr.png")
def qr_png(request: Request):
    submit_url = str(request.base_url)
    img = qrcode.make(submit_url, box_size=10, border=2)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return StreamingResponse(buf, media_type="image/png")


@app.get("/admin", response_class=HTMLResponse)
def admin_page(request: Request, credentials: HTTPBasicCredentials = Depends(security)):
    _check_admin(credentials)
    submissions = db.get_all_submissions(order="desc")
    return templates.TemplateResponse(
        "admin.html",
        {"request": request, "event_title": config.EVENT_TITLE, "submissions": submissions},
    )


@app.get("/export")
def export_text(credentials: HTTPBasicCredentials = Depends(security)):
    _check_admin(credentials)
    submissions = db.get_all_submissions(order="asc")
    lines = []
    for s in submissions:
        lines.append(f"Name: {s['name']}")
        lines.append(f"Submitted: {s['created_at']}")
        lines.append(f"Promise: {s['answer']}")
        lines.append("-" * 60)
    text = "\n".join(lines) if lines else "No submissions yet."
    return PlainTextResponse(text)


@app.get("/health")
def health():
    return {"status": "ok"}
