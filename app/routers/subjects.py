from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas.subject import SubjectCreate
from app.services import subject_service

router = APIRouter(prefix="/api/subjects", tags=["Subjects"])


@router.get("")
def get_subjects(db: Session = Depends(get_db)):
    return subject_service.get_subjects(db)


@router.post("", status_code=201)
def create_subject(subject: SubjectCreate, db: Session = Depends(get_db)):
    return subject_service.create_subject(db, subject)


@router.delete("/{subject_id}", status_code=204)
def delete_subject(subject_id: int, db: Session = Depends(get_db)):
    subject_service.delete_subject(db, subject_id)
