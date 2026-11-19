from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import rules
from app.models import Participant, Student
from app.schemas.student import StudentCreate, StudentUpdate
from app.services.school_service import find_school


def find_student(db: Session, student_id: int) -> Student:
    student = db.get(Student, student_id)
    if student is None:
        raise HTTPException(status_code=404, detail=f"Student with id {student_id} not found")
    return student


def get_students(db: Session, school_id: int | None = None, grade: int | None = None,
                 search: str | None = None) -> list:
    query = select(Student).order_by(Student.id)
    if school_id:
        query = query.where(Student.school_id == school_id)
    if grade:
        query = query.where(Student.grade == grade)
    if search:
        query = query.where((Student.first_name + " " + Student.last_name).ilike(f"%{search}%"))
    return [student.to_dict() for student in db.scalars(query)]


def create_student(db: Session, data: StudentCreate) -> dict:
    find_school(db, data.school_id)  # 404 if the school does not exist

    duplicate = db.scalar(select(Student).where(
        Student.first_name.ilike(data.first_name),
        Student.last_name.ilike(data.last_name),
        Student.school_id == data.school_id,
    ))
    if duplicate:
        raise HTTPException(status_code=409, detail="This student is already registered in this school")

    student = Student(first_name=data.first_name, last_name=data.last_name,
                      grade=data.grade, school_id=data.school_id)
    db.add(student)
    db.commit()
    db.refresh(student)
    return student.to_dict()


def update_student(db: Session, student_id: int, data: StudentUpdate) -> dict:
    student = find_student(db, student_id)
    if data.first_name is not None:
        student.first_name = data.first_name
    if data.last_name is not None:
        student.last_name = data.last_name
    if data.grade is not None:
        student.grade = data.grade
    db.commit()
    return student.to_dict()


def delete_student(db: Session, student_id: int):
    student = find_student(db, student_id)
    has_records = db.scalar(select(Participant.id).where(Participant.student_id == student_id).limit(1))
    if has_records:
        raise HTTPException(status_code=409, detail="Cannot delete a student who has olympiad records")
    db.delete(student)
    db.commit()


def get_student_history(db: Session, student_id: int) -> dict:
    """All olympiads of one student, across all years (uses the relationships)."""
    student = find_student(db, student_id)

    history = []
    for p in student.participations:
        history.append({
            "year": p.olympiad.year,
            "subject": p.subject.name,
            "status": p.status,
            "reached_round": rules.ROUNDS.get(p.current_round, "Not started"),
            "scores": p.scores,
            "place": p.place,
            "award": p.award,
        })

    history.sort(key=lambda item: item["year"], reverse=True)
    places = len([h for h in history if h["place"]])

    return {
        "student": student.first_name + " " + student.last_name,
        "school": student.school.name,
        "total_olympiads": len(history),
        "total_places": places,
        "history": history,
    }
