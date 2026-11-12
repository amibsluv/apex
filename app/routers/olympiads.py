from enum import Enum

from fastapi import APIRouter

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
def get_olympiads(status: OlympiadStatus | None = None):
    return olympiad_service.get_olympiads(status)


@router.get("/{olympiad_id}")
def get_olympiad(olympiad_id: int):
    return olympiad_service.find_olympiad(olympiad_id)


@router.post("", status_code=201)
def create_olympiad(olympiad: OlympiadCreate):
    return olympiad_service.create_olympiad(olympiad)


@router.patch("/{olympiad_id}")
def update_olympiad(olympiad_id: int, olympiad: OlympiadUpdate):
    return olympiad_service.update_olympiad(olympiad_id, olympiad)


@router.delete("/{olympiad_id}", status_code=204)
def delete_olympiad(olympiad_id: int):
    olympiad_service.delete_olympiad(olympiad_id)


@router.post("/{olympiad_id}/start", tags=["Rounds"])
def start_olympiad(olympiad_id: int):
    return olympiad_service.start_olympiad(olympiad_id)


# ---------- Participants (registration) ----------

@router.post("/{olympiad_id}/participants", status_code=201, tags=["Participants"])
def register_participant(olympiad_id: int, participant: ParticipantCreate):
    return participant_service.register_participant(olympiad_id, participant)


@router.get("/{olympiad_id}/participants", tags=["Participants"])
def get_participants(olympiad_id: int, subject_id: int | None = None,
                     school_id: int | None = None, status: ParticipantStatus | None = None):
    return participant_service.get_participants(olympiad_id, subject_id, school_id, status)


# ---------- Scores (jury uses anonymous codes) ----------

@router.get("/{olympiad_id}/scores", tags=["Rounds"])
def get_scores(olympiad_id: int, subject_id: int | None = None):
    return participant_service.get_scores(olympiad_id, subject_id)


@router.post("/{olympiad_id}/scores", status_code=201, tags=["Rounds"])
def add_score(olympiad_id: int, score: ScoreCreate):
    return participant_service.add_score(olympiad_id, score)


@router.patch("/{olympiad_id}/scores/{code}", tags=["Rounds"])
def update_score(olympiad_id: int, code: str, score: ScoreUpdate):
    return participant_service.update_score(olympiad_id, code, score)


# ---------- Rounds ----------

@router.post("/{olympiad_id}/publish-results", tags=["Rounds"])
def publish_results(olympiad_id: int):
    return round_service.publish_results(olympiad_id)


@router.post("/{olympiad_id}/close-round", tags=["Rounds"])
def close_round(olympiad_id: int):
    return round_service.close_round(olympiad_id)


# ---------- Results ----------

@router.get("/{olympiad_id}/results", tags=["Results"])
def get_results(olympiad_id: int, subject_id: int | None = None):
    return round_service.get_results(olympiad_id, subject_id)


@router.get("/{olympiad_id}/statistics", tags=["Results"])
def get_statistics(olympiad_id: int):
    return round_service.get_statistics(olympiad_id)