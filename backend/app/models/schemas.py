"""Pydantic models for API requests and responses."""
from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field

class Decision(str, Enum):
    TRUE = "TRUE"
    FALSE = "FALSE"
    MISLEADING = "MISLEADING"
    UNVERIFIED = "UNVERIFIED"
    NEEDS_CONTEXT = "NEEDS_CONTEXT"

class VerifyRequest(BaseModel):
    claim: Optional[str] = Field(None, max_length=2000)
    media_url: Optional[str] = None
    language: str = "en-US"

class Evidence(BaseModel):
    source: str
    title: str
    snippet: str
    url: str
    relevance_score: float = Field(..., ge=0.0, le=1.0)

class Source(BaseModel):
    url: str
    title: str
    credibility: float = Field(..., ge=0.0, le=1.0)

class MediaAnalysis(BaseModel):
    is_manipulated: bool
    confidence: float = Field(..., ge=0.0, le=1.0)
    findings: List[str] = []

class Citation(BaseModel):
    title: str
    url: str
    published_at: Optional[datetime] = None
    score: float = Field(..., ge=0.0, le=1.0)
    snippet: Optional[str] = Field(None, max_length=200)

class CheckScores(BaseModel):
    llm_reasoning_score: Optional[float] = None
    evidence_score: Optional[float] = None
    media_forensics_score: Optional[float] = None

class VerifyResponse(BaseModel):
    # Mobile app expects these fields
    id: str
    claim: str
    verdict: str  # Changed from 'decision'
    confidence: float = Field(..., ge=0.0, le=1.0)
    reasoning: str  # Changed from 'rationale'
    evidence: List[Evidence] = []
    sources: List[Source] = []
    media_analysis: Optional[MediaAnalysis] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Keep these for internal use
    request_id: Optional[str] = None
    checks: Optional[CheckScores] = None
    partial: Optional[bool] = False
    latency_ms: Optional[int] = None
