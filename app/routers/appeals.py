from enum import Enum

from fastapi import APIRouter

from app.schemas.appeal import AppealCreate, AppealReview
from app.services import appeal_service

router = APIRouter(tags=["Appeals"])


class AppealStatus(str, Enum):
    pending = "pending"
    accepted = "accepted"
    rejected = "rejected"


@router.post("/api/olympiads/{olympiad_id}/appeals", status_code=201)
def create_appeal(olympiad_id: int, appeal: AppealCreate):
    return appeal_service.create_appeal(olympiad_id, appeal)


@router.get("/api/olympiads/{olympiad_id}/appeals")
def get_appeals(olympiad_id: int, status: AppealStatus | None = None):
    return appeal_service.get_appeals(olympiad_id, status)


@router.get("/api/appeals/{appeal_id}")
def get_appeal(appeal_id: int):
    return appeal_service.find_appeal(appeal_id)


@router.patch("/api/appeals/{appeal_id}")
def review_appeal(appeal_id: int, review: AppealReview):
    return appeal_service.review_appeal(appeal_id, review)