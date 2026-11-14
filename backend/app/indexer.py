"""Background job: pull photos (Drive or local folder), detect faces, store embeddings + resized copies."""
import os
import traceback
from pathlib import Path
from .config import DATA_DIR, THUMB_SIDE, USE_CLAHE
from .db import SessionLocal
from .models import Event, Photo, Face
from . import cv, drive

EXT = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}


def photo_path(pid: int) -> str:
    return os.path.join(DATA_DIR, "photos", f"{pid}.jpg")


def thumb_path(pid: int) -> str:
    return os.path.join(DATA_DIR, "thumbs", f"{pid}.jpg")


def _items(ev: Event):
    """Yields (source_id, filename, loader) for every image in the event source."""
    if ev.source == "local":
        for p in sorted(Path(ev.folder).rglob("*")):
            if p.suffix.lower() in EXT:
                yield str(p), p.name, (lambda p=p: p.read_bytes())
    else:
        svc = drive.service()
        for f in drive.list_images(svc, ev.folder):
            yield f["id"], f["name"], (lambda fid=f["id"]: drive.download(svc, fid))


def index_event(event_id: int):
    db = SessionLocal()
    try:
        ev = db.get(Event, event_id)
        ev.status, ev.processed = "indexing", 0
        db.commit()
        items = list(_items(ev))
        if not items:
            raise RuntimeError(f"No images found in {ev.source} source {ev.folder!r}. "
                               "Check the path, or share the Drive folder with the service account.")
        ev.total = len(items)
        db.commit()
        done_ids = {s for (s,) in db.query(Photo.source_id).filter(Photo.event_id == event_id)}

        for source_id, name, loader in items:
            if source_id not in done_ids:  # makes re-indexing resumable
                try:
                    im = cv.load_image(loader())
                    bgr = cv.to_bgr(im)
                    photo = Photo(event_id=event_id, source_id=source_id, filename=name,
                                  width=im.width, height=im.height)
                    db.add(photo)
                    db.flush()
                    im.save(photo_path(photo.id), quality=88)
                    th = im.copy()
                    th.thumbnail((THUMB_SIDE, THUMB_SIDE))
                    th.save(thumb_path(photo.id), quality=80)
                    for f in cv.extract_faces(bgr, USE_CLAHE):
                        b = f["bbox"]
                        db.add(Face(photo_id=photo.id, embedding=f["emb"].tobytes(),
                                    x1=b[0], y1=b[1], x2=b[2], y2=b[3], score=f["score"]))
                    db.commit()
                except Exception:
                    db.rollback()
                    print(f"[index] failed on {name}")
                    traceback.print_exc()
            ev.processed += 1
            db.commit()
        ev.status = "ready"
        db.commit()
    except Exception:
        traceback.print_exc()
        db.rollback()
        ev = db.get(Event, event_id)
        if ev:
            ev.status = "error"
            db.commit()
    finally:
        db.close()
