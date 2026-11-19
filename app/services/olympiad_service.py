from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import rules
from app.models import Olympiad
from app.schemas.olympiad import OlympiadCreate, OlympiadUpdate


def find_olympiad(db: Session, olympiad_id: int) -> Olympiad:
    olympiad = db.get(Olympiad, olympiad_id)
    if olympiad is None:
        raise HTTPException(status_code=404, detail=f"Olympiad with id {olympiad_id} not found")
    return olympiad


def get_olympiads(db: Session, status: str | None = None) -> list:
    query = select(Olympiad).order_by(Olympiad.year)
    if status:
        query = query.where(Olympiad.status == status)
    return [olympiad.to_dict() for olympiad in db.scalars(query)]


def create_olympiad(db: Session, data: OlympiadCreate) -> dict:
    if db.scalar(select(Olympiad).where(Olympiad.year == data.year)):
        raise HTTPException(status_code=409,
                            detail=f"An olympiad for {data.year} already exists (only one per year)")

    olympiad = Olympiad(year=data.year, title=data.title, status="registration", current_round=0)
    db.add(olympiad)
    db.commit()
    db.refresh(olympiad)
    return olympiad.to_dict()


def update_olympiad(db: Session, olympiad_id: int, data: OlympiadUpdate) -> dict:
    olympiad = find_olympiad(db, olympiad_id)
    olympiad.title = data.title
    db.commit()
    return olympiad.to_dict()


def delete_olympiad(db: Session, olympiad_id: int):
    olympiad = find_olympiad(db, olympiad_id)
    if olympiad.status != "registration":
        raise HTTPException(status_code=409,
                            detail="Only an olympiad that has not started can be deleted")
    # its registrations are deleted too (cascade on the relationship)
    db.delete(olympiad)
    db.commit()


def start_olympiad(db: Session, olympiad_id: int) -> dict:
    olympiad = find_olympiad(db, olympiad_id)

    if olympiad.status != "registration":
        raise HTTPException(status_code=409, detail="This olympiad has already started")

    ongoing = db.scalar(select(Olympiad).where(Olympiad.status == "ongoing"))
    if ongoing:
        raise HTTPException(status_code=409,
                            detail=f"The {ongoing.year} olympiad is still ongoing. Finish it first.")

    if len(olympiad.participants) == 0:
        raise HTTPException(status_code=400, detail="Cannot start an olympiad with no participants")

    for p in olympiad.participants:
        p.status = "active"
        p.current_round = 1

    olympiad.status = "ongoing"
    olympiad.current_round = 1
    olympiad.current_round_name = rules.ROUNDS[1]
    db.commit()
    return olympiad.to_dict()
