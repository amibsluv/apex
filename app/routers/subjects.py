from fastapi import APIRouter

from app import database as db
from app.schemas.subject import SubjectCreate
from app.services import subject_service

router = APIRouter(prefix="/api/subjects", tags=["Subjects"])


@router.get("")
def get_subjects():
    return db.subjects


@router.post("", status_code=201)
def create_subject(subject: SubjectCreate):
    return subject_service.create_subject(subject)


@router.delete("/{subject_id}", status_code=204)
def delete_subject(subject_id: int):
    subject_service.delete_subject(subject_id)