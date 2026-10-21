from enum import Enum
from typing import List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field

class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    INCONCLUSIVE = "inconclusive"

class SignalSource(str, Enum):
    """The six reviews of the guide (section 11), plus the Banco de números."""
    TRADUCTOR = "traductor"
    PISTAS = "pistas"
    ENLACES = "enlaces"
    PSICOLOGO = "psicologo"
    ARCHIVISTA = "archivista"
    JUEZ = "juez"
    BANCO = "banco"

class ConfidenceLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class LinkStatus(str, Enum):
    UNCHECKED = "unchecked"
    SUSPICIOUS = "suspicious"
    FLAGGED = "flagged"
    NO_KNOWN_THREAT = "no_known_threat"
    OFFICIAL = "official"

class AnalysisInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    text: str = Field(..., min_length=1, max_length=4000, description="Contenido del mensaje a analizar")
    source: str = Field(default="telegram", description="Origen de la petición")
    tipo: Literal["mensaje", "compra", "llamada"] = Field(default="mensaje", description="Mensaje, oferta de compra o relato de una llamada")
    user_ref: Optional[str] = Field(default=None, description="Identificador seudonimizado")
    links: List[str] = Field(default_factory=list, description="URLs extraídas")
    metadata: dict = Field(default_factory=dict, description="Metadatos sin información sensible")


class SignalItem(BaseModel):
    code: str
    label: str
    evidence: str
    source: SignalSource
    confidence: ConfidenceLevel = ConfidenceLevel.HIGH
    points: int = Field(default=0, description="Puntos que sumó o restó (Rayos X)")

class LinkAnalysis(BaseModel):
    url: str
    status: LinkStatus
    reason: str

class CampaignMatch(BaseModel):
    campaign_id: str
    name: str
    similarity_pct: int
    total_reports_today: int

class AnalysisResult(BaseModel):
    risk_level: RiskLevel
    risk_score: int = Field(..., ge=0, le=100, description="Score heurístico de 0 a 100")
    summary: str
    category: Optional[str] = Field(default=None, description="Modalidad en palabras simples")
    modalidad: Optional[str] = None
    signals: List[SignalItem] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    links: List[LinkAnalysis] = Field(default_factory=list)
    recognized: List[str] = Field(default_factory=list, description="Lo que reconoció: enlaces, entidad, qué pide")
    campaign: Optional[CampaignMatch] = None
    extracted_text: Optional[str] = Field(default=None, description="Texto leído de la captura o de la nota de voz")
    limitations: List[str] = Field(default_factory=list)
    verification_id: Optional[str] = None
    processing_ms: int = 0
    analysis_version: str = "v2"
