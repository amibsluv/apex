from fastapi import HTTPException

from app import database as db
from app.schemas.school import SchoolCreate, SchoolUpdate


def find_school(school_id: int) -> dict:
    for school in db.schools:
        if school["id"] == school_id:
            return school
    raise HTTPException(status_code=404, detail=f"School with id {school_id} not found")


def get_schools(region: str | None = None, school_type: str | None = None) -> list:
    result = []
    for school in db.schools:
        if region and school["region"] != region:
            continue
        if school_type and school["school_type"] != school_type:
            continue
        result.append(school)
    return result


def create_school(data: SchoolCreate) -> dict:
    for school in db.schools:
        if school["name"].lower() == data.name.lower() and school["region"] == data.region.value:
            raise HTTPException(status_code=409, detail="This school already exists in this region")

    new_school = {
        "id": db.next_id("schools"),
        "name": data.name,
        "region": data.region.value,
        "school_type": data.school_type.value,
    }
    db.schools.append(new_school)
    return new_school


def update_school(school_id: int, data: SchoolUpdate) -> dict:
    school = find_school(school_id)
    if data.name is not None:
        school["name"] = data.name
    if data.region is not None:
        school["region"] = data.region.value
    if data.school_type is not None:
        school["school_type"] = data.school_type.value
    return school


def delete_school(school_id: int):
    school = find_school(school_id)
    for student in db.students:
        if student["school_id"] == school_id:
            raise HTTPException(status_code=409,
                                detail="Cannot delete a school that still has students")
    db.schools.remove(school)