from fastapi import HTTPException

from app import database as db
from app.schemas.participant import (DisqualifyRequest, ParticipantCreate,
                                     ScoreCreate, ScoreUpdate)
from app.services.olympiad_service import find_olympiad
from app.services.school_service import find_school
from app.services.student_service import find_student
from app.services.subject_service import find_subject


def find_participant(participant_id: int) -> dict:
    for p in db.participants:
        if p["id"] == participant_id:
            return p
    raise HTTPException(status_code=404, detail=f"Participant with id {participant_id} not found")


def find_by_code(olympiad_id: int, code: str) -> dict:
    for p in db.participants:
        if p["olympiad_id"] == olympiad_id and p["code"] == code.upper():
            return p
    raise HTTPException(status_code=404, detail=f"No participant with code {code} in this olympiad")


def with_details(p: dict) -> dict:
    """Participant together with student, school and subject names (for organizers)."""
    student = find_student(p["student_id"])
    school = find_school(student["school_id"])
    subject = find_subject(p["subject_id"])
    return {
        **p,
        "student_name": student["first_name"] + " " + student["last_name"],
        "grade": student["grade"],
        "school": school["name"],
        "school_type": school["school_type"],
        "region": school["region"],
        "subject": subject["name"],
        "round_name": db.ROUNDS.get(p["current_round"], "Not started"),
    }


def anonymous(p: dict) -> dict:
    """What the jury sees: only the code and the scores, no name."""
    return {
        "code": p["code"],
        "round": p["current_round"],
        "status": p["status"],
        "scores": p["scores"],
    }


# ---------- Workflow 1: registration ----------

def register_participant(olympiad_id: int, data: ParticipantCreate) -> dict:
    olympiad = find_olympiad(olympiad_id)
    student = find_student(data.student_id)
    subject = find_subject(data.subject_id)

    if olympiad["status"] != "registration":
        raise HTTPException(status_code=409, detail="Registration for this olympiad is closed")

    same_olympiad = [p for p in db.participants if p["olympiad_id"] == olympiad_id]

    # Rule: a student cannot be registered twice for the same subject
    for p in same_olympiad:
        if p["student_id"] == student["id"] and p["subject_id"] == subject["id"]:
            raise HTTPException(status_code=409,
                                detail="This student is already registered for this subject")

    # Rule: a student can take part in at most 2 subjects
    student_subjects = [p for p in same_olympiad if p["student_id"] == student["id"]]
    if len(student_subjects) >= db.MAX_SUBJECTS_PER_STUDENT:
        raise HTTPException(status_code=400,
                            detail=f"A student can take part in at most {db.MAX_SUBJECTS_PER_STUDENT} subjects")

    # Rule: at most 3 students from one school in one subject
    count = 0
    for p in same_olympiad:
        other = find_student(p["student_id"])
        if p["subject_id"] == subject["id"] and other["school_id"] == student["school_id"]:
            count += 1
    if count >= db.MAX_STUDENTS_PER_SCHOOL_IN_SUBJECT:
        raise HTTPException(status_code=400,
                            detail=f"A school can send at most {db.MAX_STUDENTS_PER_SCHOOL_IN_SUBJECT} "
                                   f"students in one subject")

    new_id = db.next_id("participants")
    new_participant = {
        "id": new_id,
        "olympiad_id": olympiad_id,
        "student_id": student["id"],
        "subject_id": subject["id"],
        # Anonymous code, for example MATH-2026-0007
        "code": f"{subject['name'][:4].upper()}-{olympiad['year']}-{new_id:04d}",
        "status": "registered",  # registered -> active -> eliminated / finished / disqualified
        "current_round": 0,
        "scores": {},            # round number -> {"written", "test", "total"}
        "place": None,
        "award": None,
    }
    db.participants.append(new_participant)
    return with_details(new_participant)


def get_participants(olympiad_id: int, subject_id: int | None = None,
                     school_id: int | None = None, status: str | None = None) -> list:
    find_olympiad(olympiad_id)
    result = []
    for p in db.participants:
        if p["olympiad_id"] != olympiad_id:
            continue
        if subject_id and p["subject_id"] != subject_id:
            continue
        if status and p["status"] != status:
            continue
        if school_id and find_student(p["student_id"])["school_id"] != school_id:
            continue
        result.append(with_details(p))
    return result


def withdraw_participant(participant_id: int):
    p = find_participant(participant_id)
    olympiad = find_olympiad(p["olympiad_id"])
    if olympiad["status"] != "registration":
        raise HTTPException(status_code=409,
                            detail="A student can only be withdrawn before the olympiad starts")
    db.participants.remove(p)


def disqualify_participant(participant_id: int, data: DisqualifyRequest) -> dict:
    p = find_participant(participant_id)
    if p["status"] != "active":
        raise HTTPException(status_code=409,
                            detail=f"Only active participants can be disqualified (status: {p['status']})")
    p["status"] = "disqualified"
    p["scores"] = {}  # points are cancelled
    p["disqualify_reason"] = data.reason
    return with_details(p)


# ---------- Workflow 2: scoring by anonymous code ----------

def check_can_score(olympiad: dict, p: dict):
    if olympiad["status"] != "ongoing":
        raise HTTPException(status_code=409, detail="Scores can only be entered while the olympiad is ongoing")
    if olympiad["results_published_at"] is not None:
        raise HTTPException(status_code=409,
                            detail="Results of this round are already published. Scores can only change by appeal.")
    if p["status"] != "active":
        raise HTTPException(status_code=409, detail=f"This participant is {p['status']} and cannot get scores")


def add_score(olympiad_id: int, data: ScoreCreate) -> dict:
    olympiad = find_olympiad(olympiad_id)
    p = find_by_code(olympiad_id, data.code)
    check_can_score(olympiad, p)

    round_no = olympiad["current_round"]
    if round_no in p["scores"]:
        raise HTTPException(status_code=409,
                            detail=f"Score for round {round_no} already exists. Use PATCH to correct it.")

    p["scores"][round_no] = {"written": data.written, "test": data.test,
                             "total": data.written + data.test}
    return anonymous(p)


def update_score(olympiad_id: int, code: str, data: ScoreUpdate) -> dict:
    olympiad = find_olympiad(olympiad_id)
    p = find_by_code(olympiad_id, code)
    check_can_score(olympiad, p)

    round_no = olympiad["current_round"]
    if round_no not in p["scores"]:
        raise HTTPException(status_code=404, detail="No score yet for this round. Use POST first.")

    p["scores"][round_no] = {"written": data.written, "test": data.test,
                             "total": data.written + data.test}
    return anonymous(p)


def get_scores(olympiad_id: int, subject_id: int | None = None) -> list:
    """Jury view: codes and scores only."""
    find_olympiad(olympiad_id)
    result = []
    for p in db.participants:
        if p["olympiad_id"] != olympiad_id or p["status"] != "active":
            continue
        if subject_id and p["subject_id"] != subject_id:
            continue
        result.append(anonymous(p))
    return result