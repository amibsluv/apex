from fastapi import HTTPException

from app import database as db
from app.schemas.olympiad import OlympiadCreate, OlympiadUpdate


def find_olympiad(olympiad_id: int) -> dict:
    for olympiad in db.olympiads:
        if olympiad["id"] == olympiad_id:
            return olympiad
    raise HTTPException(status_code=404, detail=f"Olympiad with id {olympiad_id} not found")


def get_olympiads(status: str | None = None) -> list:
    result = []
    for olympiad in db.olympiads:
        if status and olympiad["status"] != status:
            continue
        result.append(olympiad)
    return result


def create_olympiad(data: OlympiadCreate) -> dict:
    for olympiad in db.olympiads:
        if olympiad["year"] == data.year:
            raise HTTPException(status_code=409,
                                detail=f"An olympiad for {data.year} already exists (only one per year)")

    new_olympiad = {
        "id": db.next_id("olympiads"),
        "year": data.year,
        "title": data.title,
        "status": "registration",       # registration -> ongoing -> completed
        "current_round": 0,             # 0 = not started, then 1, 2, 3, 4
        "current_round_name": None,
        "results_published_at": None,   # time when results of the current round were announced
    }
    db.olympiads.append(new_olympiad)
    return new_olympiad


def update_olympiad(olympiad_id: int, data: OlympiadUpdate) -> dict:
    olympiad = find_olympiad(olympiad_id)
    olympiad["title"] = data.title
    return olympiad


def delete_olympiad(olympiad_id: int):
    olympiad = find_olympiad(olympiad_id)
    if olympiad["status"] != "registration":
        raise HTTPException(status_code=409,
                            detail="Only an olympiad that has not started can be deleted")

    # also delete its registrations, so no participant points to a missing olympiad
    for p in list(db.participants):
        if p["olympiad_id"] == olympiad_id:
            db.participants.remove(p)
    db.olympiads.remove(olympiad)


def start_olympiad(olympiad_id: int) -> dict:
    olympiad = find_olympiad(olympiad_id)

    if olympiad["status"] != "registration":
        raise HTTPException(status_code=409, detail="This olympiad has already started")

    for other in db.olympiads:
        if other["status"] == "ongoing":
            raise HTTPException(status_code=409,
                                detail=f"The {other['year']} olympiad is still ongoing. Finish it first.")

    registered = [p for p in db.participants if p["olympiad_id"] == olympiad_id]
    if len(registered) == 0:
        raise HTTPException(status_code=400, detail="Cannot start an olympiad with no participants")

    for p in registered:
        p["status"] = "active"
        p["current_round"] = 1

    olympiad["status"] = "ongoing"
    olympiad["current_round"] = 1
    olympiad["current_round_name"] = db.ROUNDS[1]
    return olympiad