from enum import Enum

from pydantic import BaseModel, Field, model_validator


class AppealDecision(str, Enum):
    accepted = "accepted"
    rejected = "rejected"


class AppealCreate(BaseModel):
    code: str = Field(min_length=5, examples=["MATH-2026-0001"])
    reason: str = Field(min_length=10, max_length=500,
                        examples=["My correct test answers were not counted"])


class AppealReview(BaseModel):
    decision: AppealDecision
    comment: str = Field(min_length=3, max_length=300, examples=["Two test answers were checked again"])
    new_written: float | None = Field(default=None, ge=0, le=60)
    new_test: float | None = Field(default=None, ge=0, le=40)

    # If the appeal is accepted, the new scores must be given
    @model_validator(mode="after")
    def check_new_scores(self):
        if self.decision == AppealDecision.accepted:
            if self.new_written is None or self.new_test is None:
                raise ValueError("new_written and new_test are required when the appeal is accepted")
        return self