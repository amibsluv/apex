"""Workflow 2 (continued) and 4: publishing results, closing rounds, places and results."""
from datetime import datetime

from fastapi import HTTPException

from app import database as db
from app.services.olympiad_service import find_olympiad
from app.services.participant_service import with_details


def active_participants(olympiad_id: int) -> list:
    return [p for p in db.participants
            if p["olympiad_id"] == olympiad_id and p["status"] == "active"]


def school_type_of(p: dict) -> str:
    student = next(s for s in db.students if s["id"] == p["student_id"])
    school = next(s for s in db.schools if s["id"] == student["school_id"])
    return school["school_type"]


def get_place(total: float, school_type: str) -> tuple:
    """Places are given by percentage of points (official regulations)."""
    if total >= 90:
        return 1, "1st place - Diploma and gold medal"
    if total >= 75:
        return 2, "2nd place - Diploma and silver medal"
    if total >= db.PASS_MARK[school_type]:
        return 3, "3rd place - Diploma and bronze medal"
    return None, "Certificate of Honor"


def publish_results(olympiad_id: int) -> dict:
    """Announce the results of the current round. The 24-hour appeal period starts now."""
    olympiad = find_olympiad(olympiad_id)
    if olympiad["status"] != "ongoing":
        raise HTTPException(status_code=409, detail="The olympiad is not ongoing")
    if olympiad["results_published_at"] is not None:
        raise HTTPException(status_code=409, detail="Results of this round are already published")

    round_no = olympiad["current_round"]
    missing = [p["code"] for p in active_participants(olympiad_id) if round_no not in p["scores"]]
    if missing:
        raise HTTPException(status_code=400,
                            detail=f"{len(missing)} participant(s) have no score yet: {', '.join(missing)}")

    olympiad["results_published_at"] = datetime.now()
    return {
        "message": f"Results of the {db.ROUNDS[round_no]} round are published. "
                   f"Appeals are open for {db.APPEAL_HOURS} hours.",
        "olympiad": olympiad,
    }


def close_round(olympiad_id: int) -> dict:
    """Decide who advances to the next round. After round 4, give places."""
    olympiad = find_olympiad(olympiad_id)
    if olympiad["status"] != "ongoing":
        raise HTTPException(status_code=409, detail="The olympiad is not ongoing")
    if olympiad["results_published_at"] is None:
        raise HTTPException(status_code=409, detail="Publish the results of this round first")

    for appeal in db.appeals:
        if appeal["olympiad_id"] == olympiad_id and appeal["status"] == "pending":
            raise HTTPException(status_code=409,
                                detail="There are pending appeals. Review them before closing the round.")

    round_no = olympiad["current_round"]
    advanced = []
    eliminated = []
    winners = []

    # Rounds 1 and 2: everyone who reaches the pass mark advances
    if round_no in (1, 2):
        for p in active_participants(olympiad_id):
            total = p["scores"][round_no]["total"]
            if total >= db.PASS_MARK[school_type_of(p)]:
                p["current_round"] = round_no + 1
                advanced.append(p["code"])
            else:
                p["status"] = "eliminated"
                eliminated.append(p["code"])

    # Round 3: in each subject, the best 4 from new-type schools
    # and the best 4 from general schools go to the republican round
    elif round_no == 3:
        subject_ids = {p["subject_id"] for p in active_participants(olympiad_id)}
        for subject_id in subject_ids:
            group = [p for p in active_participants(olympiad_id) if p["subject_id"] == subject_id]
            group.sort(key=lambda p: p["scores"][3]["total"], reverse=True)
            taken = {"general": 0, "new_type": 0}
            for p in group:
                kind = school_type_of(p)
                passed = p["scores"][3]["total"] >= db.PASS_MARK[kind]
                if passed and taken[kind] < db.REPUBLICAN_QUOTA[kind]:
                    taken[kind] += 1
                    p["current_round"] = 4
                    advanced.append(p["code"])
                else:
                    p["status"] = "eliminated"
                    eliminated.append(p["code"])

    # Round 4 (republican): places by percentage
    else:
        for p in active_participants(olympiad_id):
            place, award = get_place(p["scores"][4]["total"], school_type_of(p))
            p["status"] = "finished"
            p["place"] = place
            p["award"] = award
            winners.append({"code": p["code"], "place": place, "award": award})

    # Move the olympiad to the next round, or finish it
    olympiad["results_published_at"] = None
    if round_no < 4:
        olympiad["current_round"] = round_no + 1
        olympiad["current_round_name"] = db.ROUNDS[round_no + 1]
        message = (f"{db.ROUNDS[round_no]} round closed: {len(advanced)} advanced, "
                   f"{len(eliminated)} eliminated. Next: {db.ROUNDS[round_no + 1]} round.")
    else:
        olympiad["status"] = "completed"
        message = "Republican round closed. The olympiad is completed and places are given."

    return {
        "message": message,
        "advanced": advanced,
        "eliminated": eliminated,
        "winners": winners,
    }


def get_results(olympiad_id: int, subject_id: int | None = None) -> dict:
    """Final results with names (shown only after the olympiad is completed)."""
    olympiad = find_olympiad(olympiad_id)
    if olympiad["status"] != "completed":
        raise HTTPException(status_code=409,
                            detail="Final results are available only after the olympiad is completed")

    results = []
    for p in db.participants:
        if p["olympiad_id"] != olympiad_id or p["status"] != "finished":
            continue
        if subject_id and p["subject_id"] != subject_id:
            continue
        info = with_details(p)
        results.append({
            "subject": info["subject"],
            "student_name": info["student_name"],
            "school": info["school"],
            "region": info["region"],
            "final_score": p["scores"][4]["total"],
            "place": p["place"],
            "award": p["award"],
        })

    # sort by subject, then by score (highest first)
    results.sort(key=lambda r: (r["subject"], -r["final_score"]))
    return {"year": olympiad["year"], "title": olympiad["title"], "results": results}


def get_statistics(olympiad_id: int) -> dict:
    """How many participants and places each region has."""
    find_olympiad(olympiad_id)
    regions = {}
    for p in db.participants:
        if p["olympiad_id"] != olympiad_id:
            continue
        region = with_details(p)["region"]
        if region not in regions:
            regions[region] = {"region": region, "participants": 0, "places": 0}
        regions[region]["participants"] += 1
        if p["place"]:
            regions[region]["places"] += 1

    ranking = sorted(regions.values(), key=lambda r: r["places"], reverse=True)
    return {"olympiad_id": olympiad_id, "regions": ranking}