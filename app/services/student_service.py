from fastapi import HTTPException

from app import database as db
from app.schemas.student import StudentCreate, StudentUpdate
from app.services.school_service import find_school


def find_student(student_id: int) -> dict:
    for student in db.students:
        if student["id"] == student_id:
            return student
    raise HTTPException(status_code=404, detail=f"Student with id {student_id} not found")


def get_students(school_id: int | None = None, grade: int | None = None,
                 search: str | None = None) -> list:
    result = []
    for student in db.students:
        if school_id and student["school_id"] != school_id:
            continue
        if grade and student["grade"] != grade:
            continue
        full_name = student["first_name"] + " " + student["last_name"]
        if search and search.lower() not in full_name.lower():
            continue
        result.append(student)
    return result


def create_student(data: StudentCreate) -> dict:
    find_school(data.school_id)  # 404 if the school does not exist

    for student in db.students:
        if (student["first_name"].lower() == data.first_name.lower()
                and student["last_name"].lower() == data.last_name.lower()
                and student["school_id"] == data.school_id):
            raise HTTPException(status_code=409, detail="This student is already registered in this school")

    new_student = {
        "id": db.next_id("students"),
        "first_name": data.first_name,
        "last_name": data.last_name,
        "grade": data.grade,
        "school_id": data.school_id,
    }
    db.students.append(new_student)
    return new_student


def update_student(student_id: int, data: StudentUpdate) -> dict:
    student = find_student(student_id)
    if data.first_name is not None:
        student["first_name"] = data.first_name
    if data.last_name is not None:
        student["last_name"] = data.last_name
    if data.grade is not None:
        student["grade"] = data.grade
    return student


def delete_student(student_id: int):
    student = find_student(student_id)
    for p in db.participants:
        if p["student_id"] == student_id:
            raise HTTPException(status_code=409,
                                detail="Cannot delete a student who has olympiad records")
    db.students.remove(student)


def get_student_history(student_id: int) -> dict:
    """All olympiads of one student, across all years."""
    student = find_student(student_id)
    school = find_school(student["school_id"])

    history = []
    for p in db.participants:
        if p["student_id"] != student_id:
            continue
        olympiad = next(o for o in db.olympiads if o["id"] == p["olympiad_id"])
        subject = next(s for s in db.subjects if s["id"] == p["subject_id"])
        history.append({
            "year": olympiad["year"],
            "subject": subject["name"],
            "status": p["status"],
            "reached_round": db.ROUNDS.get(p["current_round"], "Not started"),
            "scores": p["scores"],
            "place": p["place"],
            "award": p["award"],
        })

    history.sort(key=lambda item: item["year"], reverse=True)
    medals = len([h for h in history if h["place"]])

    return {
        "student": student["first_name"] + " " + student["last_name"],
        "school": school["name"],
        "total_olympiads": len(history),
        "total_places": medals,
        "history": history,
    }