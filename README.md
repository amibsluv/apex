# APEX - Academic Platform for EXcellence

REST API for the **National School Olympiad of Tajikistan**, built with **FastAPI** and **Pydantic**.
The rules follow the official regulations of the Ministry of Education and Science of Tajikistan (2022).

## What it does
- Schools register their students (grades 5-11) for olympiad subjects.
- Every participant gets an **anonymous code** (for example `MATH-2026-0013`), so the jury scores fairly without seeing names.
- The olympiad has **4 rounds**: Institutional, District (city), Regional, Republican.
- After each round, the system decides automatically who advances and who is eliminated.
- Students can **appeal** their score within 24 hours.
- After the republican round, places are given by percentage of points.
- Every year's results are saved, so each student has a history.

## Database
APEX stores all data in **PostgreSQL** using **SQLAlchemy**. The tables are created with **Alembic** migrations.

| Table | Relationship |
|---|---|
| schools | one school has many students |
| students | belongs to a school; has many participations |
| subjects | has many participants |
| olympiads | has many participants and appeals |
| participants | links student + subject + olympiad; has many appeals |
| appeals | belongs to a participant |

Constraints: unique olympiad year, unique subject name, unique school per region,
grade between 5 and 11, one registration per student per subject, one appeal per round.

## How to run (Windows)
1. Install PostgreSQL and create a database called `apex`.
2. Copy `.env.example` to `.env` and set your PostgreSQL password:

        DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/apex

3. Install and create the tables:

        python -m venv .venv
        .venv\Scripts\Activate.ps1
        pip install -r requirements.txt
        alembic upgrade head
        fastapi dev app/main.py

Open **http://127.0.0.1:8000/docs** (API) or **http://127.0.0.1:8000/web/** (website).

Demo data is added automatically the first time (when the database is empty):
- **2025** olympiad (id 1): completed, with results and history
- **2026** olympiad (id 2): open for registration

Data stays after restarting the server. `POST /api/demo/reset` reloads the demo data.

## Workflows and business rules

### 1. Registration
- Grade must be between 5 and 11.
- Registration is only possible before the olympiad starts.
- A student cannot be registered twice for the same subject.
- A student can take part in at most 2 subjects.
- A school can send at most 3 students in one subject.
- Each participant automatically gets an anonymous code.

### 2. Rounds and anonymous scoring
- The jury enters scores **by code**: written work (max 60) + test (max 40) = total (max 100).
- `publish-results` announces the results; it is not possible if any score is missing.
- After publishing, scores can only change through an appeal.
- `close-round` decides who advances:
  - Rounds 1-2: students with at least **50%** (general schools) or **60%** (new-type schools) advance.
  - Round 3: in each subject, the best **4 from new-type schools** and **4 from general schools** go to the republican round.
  - Round 4: places are given (see below) and the olympiad is completed.
- A participant who breaks the rules can be **disqualified**; their points are cancelled.

### 3. Appeals
- Only after results are published, and only within **24 hours**.
- Students with **40 points or less** cannot appeal.
- Only one appeal per student per round.
- The organizer accepts (new scores are saved) or rejects the appeal.
- A round cannot be closed while appeals are pending.

### 4. Results
| Score | Place |
|---|---|
| 90-100 | 1st place - gold medal |
| 75-89 | 2nd place - silver medal |
| 50-74 (general) / 60-74 (new-type) | 3rd place - bronze medal |
| below that | Certificate of Honor |

- Final results with names are shown only after the olympiad is completed.
- Student history across all years, and statistics by region.

## Project structure
```
app/
├── main.py        # creates the app and connects the routers
├── database.py    # in-memory lists + official rules (constants)
├── seed.py        # demo data
├── schemas/       # Pydantic models (request validation)
├── services/      # business logic and rules
└── routers/       # API endpoints
```

## Main endpoints
| Method | Path | What it does |
|---|---|---|
| GET/POST | `/api/schools` | list / create schools (`?region=`, `?school_type=`) |
| GET/PATCH/DELETE | `/api/schools/{id}` | one school |
| GET/POST | `/api/students` | list / create students (`?school_id=`, `?grade=`, `?search=`) |
| GET/PATCH/DELETE | `/api/students/{id}` | one student |
| GET | `/api/students/{id}/history` | student's results in all years |
| GET/POST/DELETE | `/api/subjects` | subjects |
| GET/POST | `/api/olympiads` | list / create olympiads (`?status=`) |
| GET/PATCH/DELETE | `/api/olympiads/{id}` | one olympiad |
| POST | `/api/olympiads/{id}/start` | close registration, start round 1 |
| GET/POST | `/api/olympiads/{id}/participants` | register / list participants |
| GET/DELETE | `/api/participants/{id}` | one participant / withdraw |
| POST | `/api/participants/{id}/disqualify` | disqualify a participant |
| GET/POST | `/api/olympiads/{id}/scores` | jury view / enter a score by code |
| PATCH | `/api/olympiads/{id}/scores/{code}` | correct a score |
| POST | `/api/olympiads/{id}/publish-results` | announce results, open appeals |
| POST | `/api/olympiads/{id}/close-round` | advance students to the next round |
| GET/POST | `/api/olympiads/{id}/appeals` | list / create appeals |
| PATCH | `/api/appeals/{id}` | accept or reject an appeal |
| GET | `/api/olympiads/{id}/results` | final results and places |
| GET | `/api/olympiads/{id}/statistics` | participants and places by region |

## Status codes
- **200** OK, **201** Created, **204** Deleted
- **400** a rule is broken (for example, a score too low to appeal)
- **404** not found
- **409** conflict (duplicate, wrong stage of the olympiad)
- **422** invalid data (Pydantic validation)
