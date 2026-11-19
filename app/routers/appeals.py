from enum import Enum

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas.appeal import AppealCreate, AppealReview
from app.services import appeal_service

router = APIRouter(tags=["Appeals"])


class AppealStatus(str, Enum):
    pending = "pending"
    accepted = "accepted"
    rejected = "rejected"


@router.post("/api/olympiads/{olympiad_id}/appeals", status_code=201)
def create_appeal(olympiad_id: int, appeal: AppealCreate, db: Session = Depends(get_db)):
    return appeal_service.create_appeal(db, olympiad_id, appeal)


@router.get("/api/olympiads/{olympiad_id}/appeals")
def get_appeals(olympiad_id: int, status: AppealStatus | None = None, db: Session = Depends(get_db)):
    return appeal_service.get_appeals(db, olympiad_id, status)


@router.get("/api/appeals/{appeal_id}")
def get_appeal(appeal_id: int, db: Session = Depends(get_db)):
    return appeal_service.find_appeal(db, appeal_id).to_dict()


@router.patch("/api/appeals/{appeal_id}")
def review_appeal(appeal_id: int, review: AppealReview, db: Session = Depends(get_db)):
    return appeal_service.review_appeal(db, appeal_id, review)
