from fastapi import Depends, FastAPI
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from app.db import SessionLocal, get_db
from app.routers import appeals, olympiads, participants, schools, students, subjects
from app.seed import load_demo_data, seed_if_empty

app = FastAPI(
    title="APEX - Academic Platform for EXcellence",
    description="REST API for the National School Olympiad of Tajikistan: "
                "registration, 4 rounds with anonymous scoring, appeals and results. "
                "Data is stored in PostgreSQL.",
)

app.include_router(schools.router)
app.include_router(students.router)
app.include_router(subjects.router)
app.include_router(olympiads.router)
app.include_router(participants.router)
app.include_router(appeals.router)

# The website (HTML, CSS, JS) is served from the "web" folder at /web
app.mount("/web", StaticFiles(directory="web", html=True), name="web")


@app.on_event("startup")
def add_demo_data():
    # Demo data is added only if the database is empty,
    # so your own data stays after restarting the server.
    with SessionLocal() as db:
        seed_if_empty(db)


@app.get("/api/hello", tags=["Info"])
def hello():
    return {"message": "Welcome to APEX", "docs": "/docs"}


@app.post("/api/demo/reset", tags=["Info"])
def reset_demo_data(db: Session = Depends(get_db)):
    load_demo_data(db)
    return {"message": "Demo data has been reloaded"}
