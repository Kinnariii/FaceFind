import io
import os
import zipfile
from collections import defaultdict
import numpy as np
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from .config import DATA_DIR, MATCH_THRESHOLD, USE_CLAHE
from .db import Base, engine, get_db
from .models import User, Event, Photo, Face
from .auth import hash_pw, check_pw, make_token, current_user, admin_user
from .indexer import index_event, photo_path, thumb_path
from . import cv

os.makedirs(os.path.join(DATA_DIR, "photos"), exist_ok=True)
os.makedirs(os.path.join(DATA_DIR, "thumbs"), exist_ok=True)
Base.metadata.create_all(engine)

app = FastAPI(title="FaceFind")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


def user_json(u: User):
    return {"id": u.id, "name": u.name, "email": u.email, "is_admin": u.is_admin}


# ---------- auth ----------
@app.post("/auth/register")
async def register(
    name: str = Form(...), email: str = Form(...), password: str = Form(...),
    consent: bool = Form(...), selfies: list[UploadFile] = File(...),
    db: Session = Depends(get_db),
):
    if not consent:
        raise HTTPException(400, "Consent to face matching is required")
    if len(password) < 6:
        raise HTTPException(400, "Password must be at least 6 characters")
    email = email.strip().lower()
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(400, "That email is already registered")
    imgs = []
    for f in selfies[:3]:
        try:
            imgs.append(cv.to_bgr(cv.load_image(await f.read())))
        except Exception:
            continue
    emb = cv.user_embedding(imgs, USE_CLAHE)
    if emb is None:
        raise HTTPException(400, "No face found in your photos. Use a clear, well-lit selfie facing the camera.")
    user = User(name=name.strip(), email=email, password_hash=hash_pw(password),
                embedding=emb.tobytes(), consent=True,
                is_admin=db.query(User).count() == 0)  # first account becomes admin
    db.add(user)
    db.commit()
    return {"token": make_token(user.id), "user": user_json(user)}


class LoginIn(BaseModel):
    email: str
    password: str


@app.post("/auth/login")
def login(body: LoginIn, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == body.email.strip().lower()).first()
    if not user or not check_pw(body.password, user.password_hash):
        raise HTTPException(401, "Wrong email or password")
    return {"token": make_token(user.id), "user": user_json(user)}


@app.get("/me")
def me(user: User = Depends(current_user)):
    return user_json(user)


@app.delete("/me")
def delete_me(user: User = Depends(current_user), db: Session = Depends(get_db)):
    """Privacy: removes the account and the stored face embedding."""
    db.delete(user)
    db.commit()
    return {"deleted": True}


# ---------- events ----------
class EventIn(BaseModel):
    name: str
    source: str = "drive"  # drive | local
    folder: str


def event_json(e: Event):
    return {"id": e.id, "name": e.name, "source": e.source, "status": e.status,
            "total": e.total, "processed": e.processed}


@app.get("/events")
def list_events(user: User = Depends(current_user), db: Session = Depends(get_db)):
    return [event_json(e) for e in db.query(Event).order_by(Event.id.desc())]


@app.post("/events")
def create_event(body: EventIn, _: User = Depends(admin_user), db: Session = Depends(get_db)):
    if body.source not in ("drive", "local"):
        raise HTTPException(400, "source must be 'drive' or 'local'")
    e = Event(name=body.name.strip(), source=body.source, folder=body.folder.strip())
    db.add(e)
    db.commit()
    return event_json(e)


@app.post("/events/{eid}/index")
def start_index(eid: int, bg: BackgroundTasks, _: User = Depends(admin_user), db: Session = Depends(get_db)):
    e = db.get(Event, eid)
    if not e:
        raise HTTPException(404, "Event not found")
    if e.status == "indexing":
        raise HTTPException(400, "Already indexing")
    bg.add_task(index_event, eid)
    e.status = "indexing"
    db.commit()
    return event_json(e)


@app.get("/events/{eid}/status")
def event_status(eid: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    e = db.get(Event, eid)
    if not e:
        raise HTTPException(404, "Event not found")
    return event_json(e)


# ---------- matching ----------
def match_user(eid: int, user: User, db: Session) -> dict:
    """Returns {category: [{id, score}]} for photos in the event that contain the user."""
    rows = db.query(Face).join(Photo).filter(Photo.event_id == eid).all()
    result = {c: [] for c in cv.CATEGORIES}
    if not rows:
        return result
    u = np.frombuffer(user.embedding, dtype=np.float32)
    embs = np.stack([np.frombuffer(f.embedding, dtype=np.float32) for f in rows])
    sims = embs @ u  # cosine similarity (all vectors are L2-normalised)
    by_photo = defaultdict(list)
    for f, s in zip(rows, sims):
        by_photo[f.photo_id].append((f, float(s)))
    for pid, fs in by_photo.items():
        best, score = max(fs, key=lambda x: x[1])
        if score < MATCH_THRESHOLD:
            continue
        boxes = [[f.x1, f.y1, f.x2, f.y2] for f, _ in fs]
        cat = cv.categorize(boxes, [best.x1, best.y1, best.x2, best.y2])
        result[cat].append({"id": pid, "score": round(score, 3)})
    for c in result:
        result[c].sort(key=lambda x: -x["score"])
    return result


@app.get("/events/{eid}/my-photos")
def my_photos(eid: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    if not db.get(Event, eid):
        raise HTTPException(404, "Event not found")
    return match_user(eid, user, db)


@app.get("/events/{eid}/download")
def download_zip(eid: int, category: str | None = None, user: User = Depends(current_user),
                 db: Session = Depends(get_db)):
    res = match_user(eid, user, db)
    cats = [category] if category in res else cv.CATEGORIES
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_STORED) as z:
        for c in cats:
            for p in res[c]:
                fname = db.get(Photo, p["id"]).filename
                z.write(photo_path(p["id"]), f"{c}/{p['id']}_{fname}")
    buf.seek(0)
    name = f"my_photos_{category or 'all'}.zip"
    return StreamingResponse(buf, media_type="application/zip",
                             headers={"Content-Disposition": f'attachment; filename="{name}"'})


# ---------- media ----------
@app.get("/media/{kind}/{pid}")
def media(kind: str, pid: int, _: User = Depends(current_user)):
    path = thumb_path(pid) if kind == "thumb" else photo_path(pid)
    if not os.path.exists(path):
        raise HTTPException(404, "Not found")
    return FileResponse(path, media_type="image/jpeg", headers={"Cache-Control": "private, max-age=3600"})
