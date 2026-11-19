"""Database tables (SQLAlchemy models).

Relationships:
- School      1 ── many  Student
- Student     1 ── many  Participant
- Subject     1 ── many  Participant
- Olympiad    1 ── many  Participant
- Olympiad    1 ── many  Appeal
- Participant 1 ── many  Appeal
"""
from datetime import datetime

from sqlalchemy import (JSON, CheckConstraint, DateTime, ForeignKey, Integer,
                        String, UniqueConstraint, func)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class ToDictMixin:
    """Turns a database row into a dictionary, so it can be returned as JSON."""

    def to_dict(self) -> dict:
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}


class School(ToDictMixin, Base):
    __tablename__ = "schools"
    __table_args__ = (UniqueConstraint("name", "region", name="uq_school_name_region"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    region: Mapped[str] = mapped_column(String(20))
    school_type: Mapped[str] = mapped_column(String(20))  # "general" or "new_type"

    # one school has many students
    students: Mapped[list["Student"]] = relationship(back_populates="school")


class Student(ToDictMixin, Base):
    __tablename__ = "students"
    __table_args__ = (CheckConstraint("grade BETWEEN 5 AND 11", name="ck_student_grade"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    first_name: Mapped[str] = mapped_column(String(50))
    last_name: Mapped[str] = mapped_column(String(50))
    grade: Mapped[int] = mapped_column(Integer)
    school_id: Mapped[int] = mapped_column(ForeignKey("schools.id", ondelete="RESTRICT"))

    school: Mapped["School"] = relationship(back_populates="students")
    participations: Mapped[list["Participant"]] = relationship(back_populates="student")


class Subject(ToDictMixin, Base):
    __tablename__ = "subjects"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True)

    participants: Mapped[list["Participant"]] = relationship(back_populates="subject")


class Olympiad(ToDictMixin, Base):
    __tablename__ = "olympiads"

    id: Mapped[int] = mapped_column(primary_key=True)
    year: Mapped[int] = mapped_column(Integer, unique=True)  # one olympiad per year
    title: Mapped[str] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(20), default="registration")  # registration -> ongoing -> completed
    current_round: Mapped[int] = mapped_column(Integer, default=0)            # 0 = not started, then 1-4
    current_round_name: Mapped[str | None] = mapped_column(String(30), nullable=True)
    results_published_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # one olympiad has many participants (deleted together with the olympiad)
    participants: Mapped[list["Participant"]] = relationship(
        back_populates="olympiad", cascade="all, delete-orphan")
    appeals: Mapped[list["Appeal"]] = relationship(
        back_populates="olympiad", cascade="all, delete-orphan")


class Participant(ToDictMixin, Base):
    """One student taking part in one subject of one olympiad."""
    __tablename__ = "participants"
    __table_args__ = (
        UniqueConstraint("olympiad_id", "student_id", "subject_id", name="uq_participant"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    olympiad_id: Mapped[int] = mapped_column(ForeignKey("olympiads.id", ondelete="CASCADE"))
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id", ondelete="RESTRICT"))
    subject_id: Mapped[int] = mapped_column(ForeignKey("subjects.id", ondelete="RESTRICT"))
    code: Mapped[str | None] = mapped_column(String(30), unique=True, nullable=True)  # anonymous code
    status: Mapped[str] = mapped_column(String(20), default="registered")
    current_round: Mapped[int] = mapped_column(Integer, default=0)
    scores: Mapped[dict] = mapped_column(JSON, default=dict)  # {"1": {"written", "test", "total"}, ...}
    place: Mapped[int | None] = mapped_column(Integer, nullable=True)
    award: Mapped[str | None] = mapped_column(String(100), nullable=True)
    disqualify_reason: Mapped[str | None] = mapped_column(String(300), nullable=True)

    olympiad: Mapped["Olympiad"] = relationship(back_populates="participants")
    student: Mapped["Student"] = relationship(back_populates="participations")
    subject: Mapped["Subject"] = relationship(back_populates="participants")
    appeals: Mapped[list["Appeal"]] = relationship(
        back_populates="participant", cascade="all, delete-orphan")


class Appeal(ToDictMixin, Base):
    __tablename__ = "appeals"
    __table_args__ = (UniqueConstraint("participant_id", "round", name="uq_appeal_per_round"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    olympiad_id: Mapped[int] = mapped_column(ForeignKey("olympiads.id", ondelete="CASCADE"))
    participant_id: Mapped[int] = mapped_column(ForeignKey("participants.id", ondelete="CASCADE"))
    code: Mapped[str] = mapped_column(String(30))
    round: Mapped[int] = mapped_column(Integer)
    reason: Mapped[str] = mapped_column(String(500))
    old_score: Mapped[float] = mapped_column()
    new_score: Mapped[float | None] = mapped_column(nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending -> accepted / rejected
    comment: Mapped[str | None] = mapped_column(String(300), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    olympiad: Mapped["Olympiad"] = relationship(back_populates="appeals")
    participant: Mapped["Participant"] = relationship(back_populates="appeals")
