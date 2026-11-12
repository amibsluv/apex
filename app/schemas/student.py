from pydantic import BaseModel, Field


class StudentCreate(BaseModel):
    first_name: str = Field(min_length=2, max_length=50, examples=["Farrukh"])
    last_name: str = Field(min_length=2, max_length=50, examples=["Rahimov"])
    grade: int = Field(ge=5, le=11, examples=[10])  # olympiads are for grades 5-11
    school_id: int = Field(gt=0, examples=[1])


class StudentUpdate(BaseModel):
    first_name: str | None = Field(default=None, min_length=2, max_length=50)
    last_name: str | None = Field(default=None, min_length=2, max_length=50)
    grade: int | None = Field(default=None, ge=5, le=11)