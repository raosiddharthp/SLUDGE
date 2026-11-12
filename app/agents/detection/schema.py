"""Structured output for the Detection Agent. Gemini must return this shape."""
from enum import Enum

from pydantic import BaseModel, Field


class Driver(str, Enum):
    health = "health"
    life_events = "life_events"
    resilience = "resilience"
    capability = "capability"


class Evidence(BaseModel):
    unit_id: str = Field(description="Record ID exactly as shown in square brackets")
    quote: str = Field(description="Words copied exactly from that record")


class Finding(BaseModel):
    driver: Driver
    confidence: float = Field(description="0 to 1")
    repeat_disclosure: bool = Field(
        description="True only if the member's own words say they have already told the organisation about this"
    )
    rationale: str = Field(description="One or two plain sentences restating only what the cited records say")
    evidence: list[Evidence]


class DetectionResult(BaseModel):
    findings: list[Finding]
    note: str = Field(description="One sentence summarising the assessment")
