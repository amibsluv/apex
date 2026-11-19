from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas.school import Region, SchoolCreate, SchoolType, SchoolUpdate
from app.services import school_service

router = APIRouter(prefix="/api/schools", tags=["Schools"])


@router.get("")
def get_schools(region: Region | None = None, school_type: SchoolType | None = None, db: Session = Depends(get_db)):
    return school_service.get_schools(db, region, school_type)


@router.get("/{school_id}")
def get_school(school_id: int, db: Session = Depends(get_db)):
    return school_service.find_school(db, school_id).to_dict()


@router.post("", status_code=201)
def create_school(school: SchoolCreate, db: Session = Depends(get_db)):
    return school_service.create_school(db, school)


@router.patch("/{school_id}")
def update_school(school_id: int, school: SchoolUpdate, db: Session = Depends(get_db)):
    return school_service.update_school(db, school_id, school)


@router.delete("/{school_id}", status_code=204)
def delete_school(school_id: int, db: Session = Depends(get_db)):
    school_service.delete_school(db, school_id)
