from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Participant, Subject
from app.schemas.subject import SubjectCreate


def find_subject(db: Session, subject_id: int) -> Subject:
    subject = db.get(Subject, subject_id)
    if subject is None:
        raise HTTPException(status_code=404, detail=f"Subject with id {subject_id} not found")
    return subject


def get_subjects(db: Session) -> list:
    return [subject.to_dict() for subject in db.scalars(select(Subject).order_by(Subject.id))]


def create_subject(db: Session, data: SubjectCreate) -> dict:
    if db.scalar(select(Subject).where(Subject.name.ilike(data.name))):
        raise HTTPException(status_code=409, detail="This subject already exists")

    subject = Subject(name=data.name)
    db.add(subject)
    db.commit()
    db.refresh(subject)
    return subject.to_dict()


def delete_subject(db: Session, subject_id: int):
    subject = find_subject(db, subject_id)
    used = db.scalar(select(Participant.id).where(Participant.subject_id == subject_id).limit(1))
    if used:
        raise HTTPException(status_code=409, detail="Cannot delete a subject that has olympiad participants")
    db.delete(subject)
    db.commit()
