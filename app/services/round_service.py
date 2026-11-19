"""Publishing results, closing rounds, places and final results."""
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import rules
from app.models import Appeal, Participant
from app.services.olympiad_service import find_olympiad


def active_participants(db: Session, olympiad_id: int) -> list[Participant]:
    query = select(Participant).where(Participant.olympiad_id == olympiad_id,
                                      Participant.status == "active").order_by(Participant.id)
    return list(db.scalars(query))


def total(p: Participant, round_no: int) -> float:
    return p.scores[str(round_no)]["total"]


def get_place(score: float, school_type: str) -> tuple:
    """Places are given by percentage of points (official regulations)."""
    if score >= 90:
        return 1, "1st place - Diploma and gold medal"
    if score >= 75:
        return 2, "2nd place - Diploma and silver medal"
    if score >= rules.PASS_MARK[school_type]:
        return 3, "3rd place - Diploma and bronze medal"
    return None, "Certificate of Honor"


def publish_results(db: Session, olympiad_id: int) -> dict:
    """Announce the results of the current round. The 24-hour appeal period starts now."""
    olympiad = find_olympiad(db, olympiad_id)
    if olympiad.status != "ongoing":
        raise HTTPException(status_code=409, detail="The olympiad is not ongoing")
    if olympiad.results_published_at is not None:
        raise HTTPException(status_code=409, detail="Results of this round are already published")

    round_no = olympiad.current_round
    missing = [p.code for p in active_participants(db, olympiad_id) if str(round_no) not in p.scores]
    if missing:
        raise HTTPException(status_code=400,
                            detail=f"{len(missing)} participant(s) have no score yet: {', '.join(missing)}")

    olympiad.results_published_at = datetime.now()
    db.commit()
    return {
        "message": f"Results of the {rules.ROUNDS[round_no]} round are published. "
                   f"Appeals are open for {rules.APPEAL_HOURS} hours.",
        "olympiad": olympiad.to_dict(),
    }


def close_round(db: Session, olympiad_id: int) -> dict:
    """Decide who advances to the next round. After round 4, give places."""
    olympiad = find_olympiad(db, olympiad_id)
    if olympiad.status != "ongoing":
        raise HTTPException(status_code=409, detail="The olympiad is not ongoing")
    if olympiad.results_published_at is None:
        raise HTTPException(status_code=409, detail="Publish the results of this round first")

    pending = db.scalar(select(Appeal.id).where(Appeal.olympiad_id == olympiad_id,
                                                Appeal.status == "pending").limit(1))
    if pending:
        raise HTTPException(status_code=409,
                            detail="There are pending appeals. Review them before closing the round.")

    round_no = olympiad.current_round
    advanced, eliminated, winners = [], [], []

    # Rounds 1 and 2: everyone who reaches the pass mark advances
    if round_no in (1, 2):
        for p in active_participants(db, olympiad_id):
            if total(p, round_no) >= rules.PASS_MARK[p.student.school.school_type]:
                p.current_round = round_no + 1
                advanced.append(p.code)
            else:
                p.status = "eliminated"
                eliminated.append(p.code)

    # Round 3: in each subject, the best 4 from new-type schools
    # and the best 4 from general schools go to the republican round
    elif round_no == 3:
        everyone = active_participants(db, olympiad_id)
        subject_ids = {p.subject_id for p in everyone}
        for subject_id in subject_ids:
            group = [p for p in everyone if p.subject_id == subject_id]
            group.sort(key=lambda p: total(p, 3), reverse=True)
            taken = {"general": 0, "new_type": 0}
            for p in group:
                kind = p.student.school.school_type
                passed = total(p, 3) >= rules.PASS_MARK[kind]
                if passed and taken[kind] < rules.REPUBLICAN_QUOTA[kind]:
                    taken[kind] += 1
                    p.current_round = 4
                    advanced.append(p.code)
                else:
                    p.status = "eliminated"
                    eliminated.append(p.code)

    # Round 4 (republican): places by percentage
    else:
        for p in active_participants(db, olympiad_id):
            place, award = get_place(total(p, 4), p.student.school.school_type)
            p.status = "finished"
            p.place = place
            p.award = award
            winners.append({"code": p.code, "place": place, "award": award})

    # Move the olympiad to the next round, or finish it
    olympiad.results_published_at = None
    if round_no < 4:
        olympiad.current_round = round_no + 1
        olympiad.current_round_name = rules.ROUNDS[round_no + 1]
        message = (f"{rules.ROUNDS[round_no]} round closed: {len(advanced)} advanced, "
                   f"{len(eliminated)} eliminated. Next: {rules.ROUNDS[round_no + 1]} round.")
    else:
        olympiad.status = "completed"
        message = "Republican round closed. The olympiad is completed and places are given."

    db.commit()
    return {"message": message, "advanced": advanced, "eliminated": eliminated, "winners": winners}


def get_results(db: Session, olympiad_id: int, subject_id: int | None = None) -> dict:
    """Final results with names (shown only after the olympiad is completed)."""
    olympiad = find_olympiad(db, olympiad_id)
    if olympiad.status != "completed":
        raise HTTPException(status_code=409,
                            detail="Final results are available only after the olympiad is completed")

    results = []
    for p in olympiad.participants:
        if p.status != "finished":
            continue
        if subject_id and p.subject_id != subject_id:
            continue
        results.append({
            "subject": p.subject.name,
            "student_name": p.student.first_name + " " + p.student.last_name,
            "school": p.student.school.name,
            "region": p.student.school.region,
            "final_score": total(p, 4),
            "place": p.place,
            "award": p.award,
        })

    # sort by subject, then by score (highest first)
    results.sort(key=lambda r: (r["subject"], -r["final_score"]))
    return {"year": olympiad.year, "title": olympiad.title, "results": results}


def get_statistics(db: Session, olympiad_id: int) -> dict:
    """How many participants and places each region has."""
    olympiad = find_olympiad(db, olympiad_id)
    regions = {}
    for p in olympiad.participants:
        region = p.student.school.region
        if region not in regions:
            regions[region] = {"region": region, "participants": 0, "places": 0}
        regions[region]["participants"] += 1
        if p.place:
            regions[region]["places"] += 1

    ranking = sorted(regions.values(), key=lambda r: r["places"], reverse=True)
    return {"olympiad_id": olympiad_id, "regions": ranking}
