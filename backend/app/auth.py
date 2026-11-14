import datetime
import bcrypt
import jwt
from fastapi import Depends, HTTPException, Request, Query
from sqlalchemy.orm import Session
from .config import SECRET_KEY
from .db import get_db
from .models import User


def hash_pw(p: str) -> str:
    return bcrypt.hashpw(p.encode(), bcrypt.gensalt()).decode()


def check_pw(p: str, h: str) -> bool:
    return bcrypt.checkpw(p.encode(), h.encode())


def make_token(user_id: int) -> str:
    exp = datetime.datetime.utcnow() + datetime.timedelta(days=7)
    return jwt.encode({"sub": str(user_id), "exp": exp}, SECRET_KEY, algorithm="HS256")


def current_user(request: Request, token: str | None = Query(None), db: Session = Depends(get_db)) -> User:
    """Accepts Authorization header, or ?token= (needed for <img> tags and download links)."""
    auth = request.headers.get("authorization", "")
    t = auth[7:] if auth.lower().startswith("bearer ") else token
    if not t:
        raise HTTPException(401, "Not logged in")
    try:
        uid = int(jwt.decode(t, SECRET_KEY, algorithms=["HS256"])["sub"])
    except Exception:
        raise HTTPException(401, "Session expired, please log in again")
    user = db.get(User, uid)
    if not user:
        raise HTTPException(401, "User not found")
    return user


def admin_user(user: User = Depends(current_user)) -> User:
    if not user.is_admin:
        raise HTTPException(403, "Admins only")
    return user
