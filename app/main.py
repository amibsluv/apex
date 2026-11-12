from fastapi import FastAPI

from app.routers import appeals, olympiads, participants, schools, students, subjects
from app.seed import load_demo_data

app = FastAPI(
    title="APEX - Academic Platform for EXcellence",
    description="REST API for the National School Olympiad of Tajikistan: "
                "registration, 4 rounds with anonymous scoring, appeals and results.",
)

app.include_router(schools.router)
app.include_router(students.router)
app.include_router(subjects.router)
app.include_router(olympiads.router)
app.include_router(participants.router)
app.include_router(appeals.router)

load_demo_data()


@app.get("/api/hello", tags=["Info"])
def hello():
    return {"message": "Welcome to APEX", "docs": "/docs"}


@app.post("/api/demo/reset", tags=["Info"])
def reset_demo_data():
    load_demo_data()
    return {"message": "Demo data has been reloaded"}