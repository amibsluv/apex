from enum import Enum

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas.olympiad import OlympiadCreate, OlympiadUpdate
from app.schemas.participant import ParticipantCreate, ScoreCreate, ScoreUpdate
from app.services import olympiad_service, participant_service, round_service

router = APIRouter(prefix="/api/olympiads", tags=["Olympiads"])


class OlympiadStatus(str, Enum):
    registration = "registration"
    ongoing = "ongoing"
    completed = "completed"


class ParticipantStatus(str, Enum):
    registered = "registered"
    active = "active"
    eliminated = "eliminated"
    disqualified = "disqualified"
    finished = "finished"


# ---------- Olympiads ----------

@router.get("")
def get_olympiads(status: OlympiadStatus | None = None, db: Session = Depends(get_db)):
    return olympiad_service.get_olympiads(db, status)


@router.get("/{olympiad_id}")
def get_olympiad(olympiad_id: int, db: Session = Depends(get_db)):
    return olympiad_service.find_olympiad(db, olympiad_id).to_dict()


@router.post("", status_code=201)
def create_olympiad(olympiad: OlympiadCreate, db: Session = Depends(get_db)):
    return olympiad_service.create_olympiad(db, olympiad)


@router.patch("/{olympiad_id}")
def update_olympiad(olympiad_id: int, olympiad: OlympiadUpdate, db: Session = Depends(get_db)):
    return olympiad_service.update_olympiad(db, olympiad_id, olympiad)


@router.delete("/{olympiad_id}", status_code=204)
def delete_olympiad(olympiad_id: int, db: Session = Depends(get_db)):
    olympiad_service.delete_olympiad(db, olympiad_id)


@router.post("/{olympiad_id}/start", tags=["Rounds"])
def start_olympiad(olympiad_id: int, db: Session = Depends(get_db)):
    return olympiad_service.start_olympiad(db, olympiad_id)


# ---------- Participants (registration) ----------

@router.post("/{olympiad_id}/participants", status_code=201, tags=["Participants"])
def register_participant(olympiad_id: int, participant: ParticipantCreate, db: Session = Depends(get_db)):
    return participant_service.register_participant(db, olympiad_id, participant)


@router.get("/{olympiad_id}/participants", tags=["Participants"])
def get_participants(olympiad_id: int, subject_id: int | None = None,
                     school_id: int | None = None, status: ParticipantStatus | None = None, db: Session = Depends(get_db)):
    return participant_service.get_participants(db, olympiad_id, subject_id, school_id, status)


# ---------- Scores (jury uses anonymous codes) ----------

@router.get("/{olympiad_id}/scores", tags=["Rounds"])
def get_scores(olympiad_id: int, subject_id: int | None = None, db: Session = Depends(get_db)):
    return participant_service.get_scores(db, olympiad_id, subject_id)


@router.post("/{olympiad_id}/scores", status_code=201, tags=["Rounds"])
def add_score(olympiad_id: int, score: ScoreCreate, db: Session = Depends(get_db)):
    return participant_service.add_score(db, olympiad_id, score)


@router.patch("/{olympiad_id}/scores/{code}", tags=["Rounds"])
def update_score(olympiad_id: int, code: str, score: ScoreUpdate, db: Session = Depends(get_db)):
    return participant_service.update_score(db, olympiad_id, code, score)


# ---------- Rounds ----------

@router.post("/{olympiad_id}/publish-results", tags=["Rounds"])
def publish_results(olympiad_id: int, db: Session = Depends(get_db)):
    return round_service.publish_results(db, olympiad_id)


@router.post("/{olympiad_id}/close-round", tags=["Rounds"])
def close_round(olympiad_id: int, db: Session = Depends(get_db)):
    return round_service.close_round(db, olympiad_id)


# ---------- Results ----------

@router.get("/{olympiad_id}/results", tags=["Results"])
def get_results(olympiad_id: int, subject_id: int | None = None, db: Session = Depends(get_db)):
    return round_service.get_results(db, olympiad_id, subject_id)


@router.get("/{olympiad_id}/statistics", tags=["Results"])
def get_statistics(olympiad_id: int, db: Session = Depends(get_db)):
    return round_service.get_statistics(db, olympiad_id)
