"""Workflow 3: appeals."""
from datetime import datetime, timedelta

from fastapi import HTTPException

from app import database as db
from app.schemas.appeal import AppealCreate, AppealReview
from app.services.olympiad_service import find_olympiad
from app.services.participant_service import find_by_code


def find_appeal(appeal_id: int) -> dict:
    for appeal in db.appeals:
        if appeal["id"] == appeal_id:
            return appeal
    raise HTTPException(status_code=404, detail=f"Appeal with id {appeal_id} not found")


def create_appeal(olympiad_id: int, data: AppealCreate) -> dict:
    olympiad = find_olympiad(olympiad_id)
    p = find_by_code(olympiad_id, data.code)

    # Rule: appeals only after the results are published
    published = olympiad["results_published_at"]
    if published is None:
        raise HTTPException(status_code=409, detail="Results of this round are not published yet")

    # Rule: appeals only within 24 hours
    if datetime.now() > published + timedelta(hours=db.APPEAL_HOURS):
        raise HTTPException(status_code=409,
                            detail=f"The appeal period ({db.APPEAL_HOURS} hours) has ended")

    if p["status"] != "active":
        raise HTTPException(status_code=409, detail=f"This participant is {p['status']}")

    # Rule: students with 40 points or less cannot appeal
    round_no = olympiad["current_round"]
    total = p["scores"][round_no]["total"]
    if total < db.MIN_SCORE_FOR_APPEAL:
        raise HTTPException(status_code=400,
                            detail=f"Score {total} is too low. Only students with more than 40 points can appeal.")

    # Rule: only one appeal per participant per round
    for appeal in db.appeals:
        if appeal["participant_id"] == p["id"] and appeal["round"] == round_no:
            raise HTTPException(status_code=409, detail="An appeal for this round already exists")

    new_appeal = {
        "id": db.next_id("appeals"),
        "olympiad_id": olympiad_id,
        "participant_id": p["id"],
        "code": p["code"],
        "round": round_no,
        "reason": data.reason,
        "old_score": total,
        "new_score": None,
        "status": "pending",  # pending -> accepted / rejected
        "comment": None,
        "created_at": datetime.now(),
    }
    db.appeals.append(new_appeal)
    return new_appeal


def get_appeals(olympiad_id: int, status: str | None = None) -> list:
    find_olympiad(olympiad_id)
    result = []
    for appeal in db.appeals:
        if appeal["olympiad_id"] != olympiad_id:
            continue
        if status and appeal["status"] != status:
            continue
        result.append(appeal)
    return result


def review_appeal(appeal_id: int, data: AppealReview) -> dict:
    appeal = find_appeal(appeal_id)
    if appeal["status"] != "pending":
        raise HTTPException(status_code=409, detail="This appeal has already been reviewed")

    appeal["status"] = data.decision.value
    appeal["comment"] = data.comment

    # If accepted, the participant's score is changed
    if data.decision.value == "accepted":
        p = next(p for p in db.participants if p["id"] == appeal["participant_id"])
        new_total = data.new_written + data.new_test
        p["scores"][appeal["round"]] = {"written": data.new_written, "test": data.new_test,
                                        "total": new_total}
        appeal["new_score"] = new_total

    return appeal