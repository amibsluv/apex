"""Demo data, loaded when the server starts.

- 2025 olympiad: completed (results, history and statistics can be viewed)
- 2026 olympiad: open for registration (can be started and played in /docs)
"""
from app import database as db
from app.schemas.olympiad import OlympiadCreate
from app.schemas.participant import ParticipantCreate, ScoreCreate
from app.schemas.school import SchoolCreate
from app.schemas.student import StudentCreate
from app.schemas.subject import SubjectCreate
from app.services import (olympiad_service, participant_service, round_service,
                          school_service, student_service, subject_service)


def load_demo_data():
    db.clear_all()

    # Schools
    for name, region, school_type in [
        ("Presidential School for Gifted Children", "Dushanbe", "new_type"),
        ("Lyceum No. 1", "Sughd", "new_type"),
        ("School No. 5", "Khatlon", "general"),
        ("School No. 12", "GBAO", "general"),
    ]:
        school_service.create_school(SchoolCreate(name=name, region=region, school_type=school_type))

    # Subjects
    for name in ["Mathematics", "Physics", "Informatics"]:
        subject_service.create_subject(SubjectCreate(name=name))

    # Students (3 in each school)
    for first, last, grade, school_id in [
        ("Farrukh", "Rahimov", 10, 1), ("Madina", "Saidova", 11, 1), ("Behruz", "Nazarov", 9, 1),
        ("Zarina", "Karimova", 10, 2), ("Firdavs", "Usmonov", 11, 2), ("Nilufar", "Sharipova", 9, 2),
        ("Daler", "Khasanov", 10, 3), ("Sitora", "Mirzoeva", 11, 3), ("Jamshed", "Odinaev", 10, 3),
        ("Parvina", "Qurbonova", 11, 4), ("Shohruh", "Davlatov", 10, 4), ("Mehrona", "Azizova", 9, 4),
    ]:
        student_service.create_student(StudentCreate(first_name=first, last_name=last,
                                                     grade=grade, school_id=school_id))

    # ----- 2025: play the whole olympiad (4 rounds) -----
    olympiad = olympiad_service.create_olympiad(
        OlympiadCreate(year=2025, title="National School Olympiad 2025"))
    for student_id in range(1, 13):
        participant_service.register_participant(
            olympiad["id"], ParticipantCreate(student_id=student_id, subject_id=1))
    olympiad_service.start_olympiad(olympiad["id"])

    for round_no in range(1, 5):
        for p in round_service.active_participants(olympiad["id"]):
            written = 30 + (p["id"] * 7 + round_no * 5) % 31   # between 30 and 60
            test = 15 + (p["id"] * 3 + round_no) % 26          # between 15 and 40
            participant_service.add_score(olympiad["id"],
                                          ScoreCreate(code=p["code"], written=written, test=test))
        round_service.publish_results(olympiad["id"])
        round_service.close_round(olympiad["id"])

    # ----- 2026: open for registration -----
    olympiad = olympiad_service.create_olympiad(
        OlympiadCreate(year=2026, title="National School Olympiad 2026"))
    for student_id in range(1, 10):
        participant_service.register_participant(
            olympiad["id"], ParticipantCreate(student_id=student_id, subject_id=1))
    for student_id in range(4, 10):
        participant_service.register_participant(
            olympiad["id"], ParticipantCreate(student_id=student_id, subject_id=3))