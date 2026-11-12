from pydantic import BaseModel, Field


class OlympiadCreate(BaseModel):
    year: int = Field(ge=2000, le=2100, examples=[2026])
    title: str = Field(min_length=3, max_length=100, examples=["National School Olympiad 2026"])


class OlympiadUpdate(BaseModel):
    title: str = Field(min_length=3, max_length=100)