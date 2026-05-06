from pydantic import BaseModel, Field
from typing import Optional

class Location(BaseModel):
    city: Optional[str] = None
    zipCode: Optional[str] = None
    country: Optional[str] = None

class Program(BaseModel):
    id: Optional[int] = None
    name: Optional[str] = None

class Event(BaseModel):
    name: Optional[str] = None
    sku: Optional[str] = None

class Time(BaseModel):
    start: Optional[str] = None
    end: Optional[str] = None

class Team(BaseModel):
    name: Optional[str] = None
    number: Optional[str] = None

class Filter(BaseModel):
    location: Optional[Location] = None
    program: Optional[Program] = None
    event: Optional[Event] = None
    season_id: Optional[int] = None
    time: Optional[Time] = None
    team: Optional[Team] = None

class SearchQuery(BaseModel):
    entity: Optional[str] = Field(None, pattern="^(team|event|matches)$")
    filter: Optional[Filter] = None
    orderBy: Optional[str] = Field(None, pattern="^(ranking|score|time)$")
    selectTop: Optional[int] = None