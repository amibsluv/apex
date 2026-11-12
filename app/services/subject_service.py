from fastapi import HTTPException

from app import database as db
from app.schemas.subject import SubjectCreate


def find_subject(subject_id: int) -> dict:
    for subject in db.subjects:
        if subject["id"] == subject_id:
            return subject
    raise HTTPException(status_code=404, detail=f"Subject with id {subject_id} not found")


def create_subject(data: SubjectCreate) -> dict:
    for subject in db.subjects:
        if subject["name"].lower() == data.name.lower():
            raise HTTPException(status_code=409, detail="This subject already exists")

    new_subject = {"id": db.next_id("subjects"), "name": data.name}
    db.subjects.append(new_subject)
    return new_subject


def delete_subject(subject_id: int):
    subject = find_subject(subject_id)
    for p in db.participants:
        if p["subject_id"] == subject_id:
            raise HTTPException(status_code=409,
                                detail="Cannot delete a subject that has olympiad participants")
    db.subjects.remove(subject)