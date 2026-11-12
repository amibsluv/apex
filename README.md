# APEX - Academic Platform for EXcellence

REST API for the **National School Olympiad of Tajikistan**, built with **FastAPI** and **Pydantic**.
The rules follow the official regulations of the Ministry of Education and Science of Tajikistan.

## What it does
- Schools register their students (grades 5-11) for olympiad subjects.
- Every participant gets an **anonymous code** (for example `MATH-2026-0013`), so the jury scores fairly without seeing names.
- The olympiad has **4 rounds**: Institutional, District (city), Regional, Republican.
- After each round, the system decides automatically who advances and who is eliminated.
- Students can **appeal** their score within 24 hours.
- After the republican round, places are given by percentage of points.
- Every year's results are saved, so each student has a history.

## How to run (Windows)
    python -m venv .venv
    .venv\Scripts\Activate.ps1
    pip install -r requirements.txt
    fastapi dev app/main.py

Open **http://127.0.0.1:8000/docs** to test all endpoints.

Demo data is loaded automatically:
- **2025** olympiad (id 1): completed, with results and history
- **2026** olympiad (id 2): open for registration, ready to be played

## Workflows and business rules

### 1. Registration
- Grade must be between 5 and 11.
- Registration is only possible before the olympiad starts.
- A student cannot be registered twice for the same subject.
- A student can take part in at most 2 subjects.
- A school can send at most 3 students in one subject.

### 2. Rounds and anonymous scoring
- The jury enters scores **by code**: written work (max 60) + test (max 40) = total (max 100).
- Results can be published only when every participant has a score.
- After publishing, scores can only change through an appeal.
- Rounds 1-2: students with at least **50%** (general schools) or **60%** (new-type schools) advance.
- Round 3: in each subject, the best **4 from new-type** and **4 from general** schools go to the republican round.
- A participant who breaks the rules can be **disqualified**; their points are cancelled.

### 3. Appeals
- Only after results are published, and only within **24 hours**.
- Students with **40 points or less** cannot appeal.
- Only one appeal per student per round.
- A round cannot be closed while appeals are pending.

### 4. Results
| Score | Place |
|---|---|
| 90-100 | 1st place - gold medal |
| 75-89 | 2nd place - silver medal |
| 50-74 (general) / 60-74 (new-type) | 3rd place - bronze medal |
| below that | Certificate of Honor |

## Project structure
    app/
    ├── main.py        # creates the app and connects the routers
    ├── database.py    # in-memory lists + official rules
    ├── seed.py        # demo data
    ├── schemas/       # Pydantic models (validation)
    ├── services/      # business logic
    └── routers/       # API endpoints

## Status codes
- **200** OK, **201** Created, **204** Deleted
- **400** a rule is broken
- **404** not found
- **409** conflict (duplicate or wrong stage)
- **422** invalid data