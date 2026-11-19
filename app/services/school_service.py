from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import School, Student
from app.schemas.school import SchoolCreate, SchoolUpdate


def find_school(db: Session, school_id: int) -> School:
    school = db.get(School, school_id)
    if school is None:
        raise HTTPException(status_code=404, detail=f"School with id {school_id} not found")
    return school


def get_schools(db: Session, region: str | None = None, school_type: str | None = None) -> list:
    query = select(School).order_by(School.id)
    if region:
        query = query.where(School.region == region)
    if school_type:
        query = query.where(School.school_type == school_type)
    return [school.to_dict() for school in db.scalars(query)]


def check_unique(db: Session, name: str, region: str, exclude_id: int | None = None):
    query = select(School).where(School.name.ilike(name), School.region == region)
    for school in db.scalars(query):
        if school.id != exclude_id:
            raise HTTPException(status_code=409, detail="This school already exists in this region")


def create_school(db: Session, data: SchoolCreate) -> dict:
    check_unique(db, data.name, data.region.value)
    school = School(name=data.name, region=data.region.value, school_type=data.school_type.value)
    db.add(school)
    db.commit()
    db.refresh(school)
    return school.to_dict()


def update_school(db: Session, school_id: int, data: SchoolUpdate) -> dict:
    school = find_school(db, school_id)
    new_name = data.name if data.name is not None else school.name
    new_region = data.region.value if data.region is not None else school.region
    check_unique(db, new_name, new_region, exclude_id=school.id)

    school.name = new_name
    school.region = new_region
    if data.school_type is not None:
        school.school_type = data.school_type.value
    db.commit()
    return school.to_dict()


def delete_school(db: Session, school_id: int):
    school = find_school(db, school_id)
    has_students = db.scalar(select(Student.id).where(Student.school_id == school_id).limit(1))
    if has_students:
        raise HTTPException(status_code=409, detail="Cannot delete a school that still has students")
    db.delete(school)
    db.commit()
