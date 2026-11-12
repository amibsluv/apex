from fastapi import APIRouter, Query

from app.schemas.student import StudentCreate, StudentUpdate
from app.services import student_service

router = APIRouter(prefix="/api/students", tags=["Students"])


@router.get("")
def get_students(school_id: int | None = None,
                 grade: int | None = Query(default=None, ge=5, le=11),
                 search: str | None = None):
    return student_service.get_students(school_id, grade, search)


@router.get("/{student_id}")
def get_student(student_id: int):
    return student_service.find_student(student_id)


@router.get("/{student_id}/history")
def get_student_history(student_id: int):
    return student_service.get_student_history(student_id)


@router.post("", status_code=201)
def create_student(student: StudentCreate):
    return student_service.create_student(student)


@router.patch("/{student_id}")
def update_student(student_id: int, student: StudentUpdate):
    return student_service.update_student(student_id, student)


@router.delete("/{student_id}", status_code=204)
def delete_student(student_id: int):
    student_service.delete_student(student_id)