"""Workflow 3: appeals."""
from datetime import datetime, timedelta

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import rules
from app.models import Appeal
from app.schemas.appeal import AppealCreate, AppealReview
from app.services.olympiad_service import find_olympiad
from app.services.participant_service import find_by_code, save_score


def find_appeal(db: Session, appeal_id: int) -> Appeal:
    appeal = db.get(Appeal, appeal_id)
    if appeal is None:
        raise HTTPException(status_code=404, detail=f"Appeal with id {appeal_id} not found")
    return appeal


def create_appeal(db: Session, olympiad_id: int, data: AppealCreate) -> dict:
    olympiad = find_olympiad(db, olympiad_id)
    p = find_by_code(db, olympiad_id, data.code)

    # Rule: appeals only after the results are published
    published = olympiad.results_published_at
    if published is None:
        raise HTTPException(status_code=409, detail="Results of this round are not published yet")

    # Rule: appeals only within 24 hours
    if datetime.now() > published + timedelta(hours=rules.APPEAL_HOURS):
        raise HTTPException(status_code=409,
                            detail=f"The appeal period ({rules.APPEAL_HOURS} hours) has ended")

    if p.status != "active":
        raise HTTPException(status_code=409, detail=f"This participant is {p.status}")

    # Rule: students with 40 points or less cannot appeal
    round_no = olympiad.current_round
    score = p.scores[str(round_no)]["total"]
    if score < rules.MIN_SCORE_FOR_APPEAL:
        raise HTTPException(status_code=400,
                            detail=f"Score {score} is too low. Only students with more than 40 points can appeal.")

    # Rule: only one appeal per participant per round
    exists = db.scalar(select(Appeal.id).where(Appeal.participant_id == p.id, Appeal.round == round_no))
    if exists:
        raise HTTPException(status_code=409, detail="An appeal for this round already exists")

    appeal = Appeal(olympiad_id=olympiad_id, participant_id=p.id, code=p.code, round=round_no,
                    reason=data.reason, old_score=score, status="pending")
    db.add(appeal)
    db.commit()
    db.refresh(appeal)
    return appeal.to_dict()


def get_appeals(db: Session, olympiad_id: int, status: str | None = None) -> list:
    find_olympiad(db, olympiad_id)
    query = select(Appeal).where(Appeal.olympiad_id == olympiad_id).order_by(Appeal.id)
    if status:
        query = query.where(Appeal.status == status)
    return [appeal.to_dict() for appeal in db.scalars(query)]


def review_appeal(db: Session, appeal_id: int, data: AppealReview) -> dict:
    appeal = find_appeal(db, appeal_id)
    if appeal.status != "pending":
        raise HTTPException(status_code=409, detail="This appeal has already been reviewed")

    appeal.status = data.decision.value
    appeal.comment = data.comment

    # If accepted, the participant's score is changed
    if data.decision.value == "accepted":
        save_score(appeal.participant, appeal.round, data.new_written, data.new_test)
        appeal.new_score = data.new_written + data.new_test

    db.commit()
    return appeal.to_dict()
