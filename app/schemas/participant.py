from pydantic import BaseModel, Field


class ParticipantCreate(BaseModel):
    student_id: int = Field(gt=0, examples=[1])
    subject_id: int = Field(gt=0, examples=[1])


class ScoreCreate(BaseModel):
    # The jury only knows the anonymous code, not the student's name
    code: str = Field(min_length=5, examples=["MATH-2026-0001"])
    written: float = Field(ge=0, le=60, examples=[45])  # written work: up to 60 points
    test: float = Field(ge=0, le=40, examples=[30])     # test: up to 40 points


class ScoreUpdate(BaseModel):
    written: float = Field(ge=0, le=60)
    test: float = Field(ge=0, le=40)


class DisqualifyRequest(BaseModel):
    reason: str = Field(min_length=5, max_length=300, examples=["Used a phone during the olympiad"])
