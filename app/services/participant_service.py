from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import rules
from app.models import Participant, Student
from app.schemas.participant import (DisqualifyRequest, ParticipantCreate,
                                     ScoreCreate, ScoreUpdate)
from app.services.olympiad_service import find_olympiad
from app.services.student_service import find_student
from app.services.subject_service import find_subject


def find_participant(db: Session, participant_id: int) -> Participant:
    p = db.get(Participant, participant_id)
    if p is None:
        raise HTTPException(status_code=404, detail=f"Participant with id {participant_id} not found")
    return p


def find_by_code(db: Session, olympiad_id: int, code: str) -> Participant:
    p = db.scalar(select(Participant).where(Participant.olympiad_id == olympiad_id,
                                            Participant.code == code.upper()))
    if p is None:
        raise HTTPException(status_code=404, detail=f"No participant with code {code} in this olympiad")
    return p


def with_details(p: Participant) -> dict:
    """Participant together with student, school and subject names (for organizers)."""
    return {
        **p.to_dict(),
        "student_name": p.student.first_name + " " + p.student.last_name,
        "grade": p.student.grade,
        "school": p.student.school.name,
        "school_type": p.student.school.school_type,
        "region": p.student.school.region,
        "subject": p.subject.name,
        "round_name": rules.ROUNDS.get(p.current_round, "Not started"),
    }


def anonymous(p: Participant) -> dict:
    """What the jury sees: only the code and the scores, no name."""
    return {"code": p.code, "round": p.current_round, "status": p.status, "scores": p.scores}


# ---------- Workflow 1: registration ----------

def register_participant(db: Session, olympiad_id: int, data: ParticipantCreate) -> dict:
    olympiad = find_olympiad(db, olympiad_id)
    student = find_student(db, data.student_id)
    subject = find_subject(db, data.subject_id)

    if olympiad.status != "registration":
        raise HTTPException(status_code=409, detail="Registration for this olympiad is closed")

    same_olympiad = olympiad.participants

    # Rule: a student cannot be registered twice for the same subject
    for p in same_olympiad:
        if p.student_id == student.id and p.subject_id == subject.id:
            raise HTTPException(status_code=409,
                                detail="This student is already registered for this subject")

    # Rule: a student can take part in at most 2 subjects
    student_subjects = [p for p in same_olympiad if p.student_id == student.id]
    if len(student_subjects) >= rules.MAX_SUBJECTS_PER_STUDENT:
        raise HTTPException(status_code=400,
                            detail=f"A student can take part in at most {rules.MAX_SUBJECTS_PER_STUDENT} subjects")

    # Rule: at most 3 students from one school in one subject
    count = 0
    for p in same_olympiad:
        if p.subject_id == subject.id and p.student.school_id == student.school_id:
            count += 1
    if count >= rules.MAX_STUDENTS_PER_SCHOOL_IN_SUBJECT:
        raise HTTPException(status_code=400,
                            detail=f"A school can send at most {rules.MAX_STUDENTS_PER_SCHOOL_IN_SUBJECT} "
                                   f"students in one subject")

    participant = Participant(olympiad_id=olympiad.id, student_id=student.id, subject_id=subject.id,
                              status="registered", current_round=0, scores={})
    db.add(participant)
    db.flush()  # gets the new id from the database
    # Anonymous code, for example MATH-2026-0007
    participant.code = f"{subject.name[:4].upper()}-{olympiad.year}-{participant.id:04d}"
    db.commit()
    db.refresh(participant)
    return with_details(participant)


def get_participants(db: Session, olympiad_id: int, subject_id: int | None = None,
                     school_id: int | None = None, status: str | None = None) -> list:
    find_olympiad(db, olympiad_id)
    query = select(Participant).where(Participant.olympiad_id == olympiad_id).order_by(Participant.id)
    if subject_id:
        query = query.where(Participant.subject_id == subject_id)
    if status:
        query = query.where(Participant.status == status)
    if school_id:
        query = query.join(Student).where(Student.school_id == school_id)
    return [with_details(p) for p in db.scalars(query)]


def withdraw_participant(db: Session, participant_id: int):
    p = find_participant(db, participant_id)
    if p.olympiad.status != "registration":
        raise HTTPException(status_code=409,
                            detail="A student can only be withdrawn before the olympiad starts")
    db.delete(p)
    db.commit()


def disqualify_participant(db: Session, participant_id: int, data: DisqualifyRequest) -> dict:
    p = find_participant(db, participant_id)
    if p.status != "active":
        raise HTTPException(status_code=409,
                            detail=f"Only active participants can be disqualified (status: {p.status})")
    p.status = "disqualified"
    p.scores = {}  # points are cancelled
    p.disqualify_reason = data.reason
    db.commit()
    return with_details(p)


# ---------- Workflow 2: scoring by anonymous code ----------

def check_can_score(olympiad, p: Participant):
    if olympiad.status != "ongoing":
        raise HTTPException(status_code=409, detail="Scores can only be entered while the olympiad is ongoing")
    if olympiad.results_published_at is not None:
        raise HTTPException(status_code=409,
                            detail="Results of this round are already published. Scores can only change by appeal.")
    if p.status != "active":
        raise HTTPException(status_code=409, detail=f"This participant is {p.status} and cannot get scores")


def save_score(p: Participant, round_no: int, written: float, test: float):
    # JSON keys are text, so the round number is stored as "1", "2"...
    # A new dictionary is assigned so SQLAlchemy notices the change.
    p.scores = {**p.scores, str(round_no): {"written": written, "test": test, "total": written + test}}


def add_score(db: Session, olympiad_id: int, data: ScoreCreate) -> dict:
    olympiad = find_olympiad(db, olympiad_id)
    p = find_by_code(db, olympiad_id, data.code)
    check_can_score(olympiad, p)

    round_no = olympiad.current_round
    if str(round_no) in p.scores:
        raise HTTPException(status_code=409,
                            detail=f"Score for round {round_no} already exists. Use PATCH to correct it.")

    save_score(p, round_no, data.written, data.test)
    db.commit()
    return anonymous(p)


def update_score(db: Session, olympiad_id: int, code: str, data: ScoreUpdate) -> dict:
    olympiad = find_olympiad(db, olympiad_id)
    p = find_by_code(db, olympiad_id, code)
    check_can_score(olympiad, p)

    round_no = olympiad.current_round
    if str(round_no) not in p.scores:
        raise HTTPException(status_code=404, detail="No score yet for this round. Use POST first.")

    save_score(p, round_no, data.written, data.test)
    db.commit()
    return anonymous(p)


def get_scores(db: Session, olympiad_id: int, subject_id: int | None = None) -> list:
    """Jury view: codes and scores only."""
    find_olympiad(db, olympiad_id)
    query = select(Participant).where(Participant.olympiad_id == olympiad_id,
                                      Participant.status == "active").order_by(Participant.id)
    if subject_id:
        query = query.where(Participant.subject_id == subject_id)
    return [anonymous(p) for p in db.scalars(query)]
