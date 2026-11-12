from fastapi import APIRouter

from app.schemas.school import Region, SchoolCreate, SchoolType, SchoolUpdate
from app.services import school_service

router = APIRouter(prefix="/api/schools", tags=["Schools"])


@router.get("")
def get_schools(region: Region | None = None, school_type: SchoolType | None = None):
    return school_service.get_schools(region, school_type)


@router.get("/{school_id}")
def get_school(school_id: int):
    return school_service.find_school(school_id)


@router.post("", status_code=201)
def create_school(school: SchoolCreate):
    return school_service.create_school(school)


@router.patch("/{school_id}")
def update_school(school_id: int, school: SchoolUpdate):
    return school_service.update_school(school_id, school)


@router.delete("/{school_id}", status_code=204)
def delete_school(school_id: int):
    school_service.delete_school(school_id)