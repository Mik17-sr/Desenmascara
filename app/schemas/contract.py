from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, HttpUrl

class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    INCONCLUSIVE = "inconclusive"

class SignalSource(str, Enum):
    RULE = "rule"
    REPUTATION = "reputation"
    MODEL = "model"

class ConfidenceLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class LinkStatus(str, Enum):
    UNCHECKED = "unchecked"
    SUSPICIOUS = "suspicious"
    FLAGGED = "flagged"
    NO_KNOWN_THREAT = "no_known_threat"

class AnalysisInput(BaseModel):
    text: str = Field(..., max_length=4000, description="Contenido del mensaje a analizar")
    source: str = Field(default="telegram", description="Origen de la petición")
    user_ref: Optional[str] = Field(default=None, description="Identificador seudonimizado")
    links: List[str] = Field(default_factory=list, description="URLs extraídas")
    metadata: dict = Field(default_factory=dict, description="Metadatos sin información sensible")


class SignalItem(BaseModel):
    code: str
    label: str
    evidence: str
    source: SignalSource
    confidence: ConfidenceLevel

class LinkAnalysis(BaseModel):
    url: str
    status: LinkStatus
    reason: str

class AnalysisResult(BaseModel):
    risk_level: RiskLevel
    risk_score: int = Field(..., ge=0, le=100, description="Score heurístico de 0 a 100")
    summary: str
    signals: List[SignalItem] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    links: List[LinkAnalysis] = Field(default_factory=list)
    limitations: List[str] = Field(default_factory=list)
    analysis_version: str = "v1"