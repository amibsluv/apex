from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas.student import StudentCreate, StudentUpdate
from app.services import student_service

router = APIRouter(prefix="/api/students", tags=["Students"])


@router.get("")
def get_students(school_id: int | None = None,
                 grade: int | None = Query(default=None, ge=5, le=11),
                 search: str | None = None, db: Session = Depends(get_db)):
    return student_service.get_students(db, school_id, grade, search)


@router.get("/{student_id}")
def get_student(student_id: int, db: Session = Depends(get_db)):
    return student_service.find_student(db, student_id).to_dict()


@router.get("/{student_id}/history")
def get_student_history(student_id: int, db: Session = Depends(get_db)):
    return student_service.get_student_history(db, student_id)


@router.post("", status_code=201)
def create_student(student: StudentCreate, db: Session = Depends(get_db)):
    return student_service.create_student(db, student)


@router.patch("/{student_id}")
def update_student(student_id: int, student: StudentUpdate, db: Session = Depends(get_db)):
    return student_service.update_student(db, student_id, student)


@router.delete("/{student_id}", status_code=204)
def delete_student(student_id: int, db: Session = Depends(get_db)):
    student_service.delete_student(db, student_id)
