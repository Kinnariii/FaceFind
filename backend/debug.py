"""Diagnose why matching returns nothing.   Run from backend/:  python debug.py"""
import numpy as np
from collections import defaultdict
from app.db import SessionLocal
from app.models import User, Event, Photo, Face
from app.config import MATCH_THRESHOLD

db = SessionLocal()
print(f"Threshold in use: {MATCH_THRESHOLD}\n")

print("== Events ==")
for e in db.query(Event):
    n_ph = db.query(Photo).filter(Photo.event_id == e.id).count()
    n_fc = db.query(Face).join(Photo).filter(Photo.event_id == e.id).count()
    no_face = n_ph - db.query(Photo.id).join(Face).filter(Photo.event_id == e.id).distinct().count()
    print(f"[{e.id}] {e.name}: status={e.status}, listed={e.total}, stored photos={n_ph}, "
          f"faces={n_fc}, photos with 0 faces={no_face}")
    if n_ph < e.total:
        print(f"    -> {e.total - n_ph} photos FAILED to index. Check the uvicorn terminal for 'failed on' tracebacks.")
    if n_fc == 0:
        print("    -> NO faces stored. Detection/indexing is the problem, not the threshold.")

print("\n== Users: best similarity per event photo ==")
for u in db.query(User):
    ue = np.frombuffer(u.embedding, dtype=np.float32)
    print(f"\nUser {u.name} <{u.email}>  (embedding norm={np.linalg.norm(ue):.3f})")
    rows = db.query(Face, Photo).join(Photo, Face.photo_id == Photo.id).all()
    if not rows:
        print("  no faces in DB"); continue
    best = defaultdict(lambda: (-1.0, ""))
    for f, p in rows:
        s = float(ue @ np.frombuffer(f.embedding, dtype=np.float32))
        if s > best[p.id][0]:
            best[p.id] = (s, p.filename)
    top = sorted(best.values(), reverse=True)[:10]
    for s, name in top:
        print(f"  {s:.3f}  {'MATCH' if s >= MATCH_THRESHOLD else '     '}  {name}")
    scores = np.array([v[0] for v in best.values()])
    print(f"  photos >= threshold: {(scores >= MATCH_THRESHOLD).sum()} / {len(scores)}   max={scores.max():.3f}")