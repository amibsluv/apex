from enum import Enum

from pydantic import BaseModel, Field


class Region(str, Enum):
    dushanbe = "Dushanbe"
    sughd = "Sughd"
    khatlon = "Khatlon"
    gbao = "GBAO"
    drs = "DRS"


class SchoolType(str, Enum):
    general = "general"    # general secondary school
    new_type = "new_type"  # Presidential school, lyceum or gymnasium


class SchoolCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100, examples=["Lyceum No. 1"])
    region: Region
    school_type: SchoolType


class SchoolUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=100)
    region: Region | None = None
    school_type: SchoolType | None = None