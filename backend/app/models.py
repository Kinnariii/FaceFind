from sqlalchemy import Column, Integer, String, Boolean, LargeBinary, Float, ForeignKey
from sqlalchemy.orm import relationship
from .db import Base


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    embedding = Column(LargeBinary, nullable=False)  # 512 x float32, L2-normalised
    consent = Column(Boolean, default=False)
    is_admin = Column(Boolean, default=False)


class Event(Base):
    __tablename__ = "events"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    source = Column(String, default="drive")  # "drive" or "local"
    folder = Column(String, nullable=False)   # Drive folder id or local path
    status = Column(String, default="new")    # new | indexing | ready | error
    total = Column(Integer, default=0)
    processed = Column(Integer, default=0)
    photos = relationship("Photo", cascade="all, delete-orphan")


class Photo(Base):
    __tablename__ = "photos"
    id = Column(Integer, primary_key=True)
    event_id = Column(Integer, ForeignKey("events.id"), index=True)
    source_id = Column(String, index=True)  # Drive file id or local path
    filename = Column(String)
    width = Column(Integer)
    height = Column(Integer)
    faces = relationship("Face", cascade="all, delete-orphan")


class Face(Base):
    __tablename__ = "faces"
    id = Column(Integer, primary_key=True)
    photo_id = Column(Integer, ForeignKey("photos.id"), index=True)
    embedding = Column(LargeBinary, nullable=False)
    x1 = Column(Integer)
    y1 = Column(Integer)
    x2 = Column(Integer)
    y2 = Column(Integer)
    score = Column(Float)
