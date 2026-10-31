from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field

class PatientBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Full name of patient")
    patient_id: str = Field(..., min_length=1, max_length=64, description="Unique medical ID of patient")
    age: Optional[int] = Field(None, ge=0, le=130, description="Patient age in years")
    date_of_birth: Optional[str] = Field(None, max_length=32, description="Date of birth (YYYY-MM-DD)")
    gender: Optional[str] = Field("Not Specified", max_length=32)
    contact_number: Optional[str] = Field(None, max_length=32, description="Contact phone number")
    email: Optional[str] = Field(None, max_length=255, description="Patient email address")
    medical_history: Optional[str] = Field(None, max_length=5000, description="Relevant general medical history")
    dental_history: Optional[str] = Field(None, max_length=5000, description="Relevant dental and periodontal history")
    notes: Optional[str] = Field(None, max_length=2000, description="Clinical or anamnesis notes")

class PatientCreate(PatientBase):
    pass

class PatientUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    age: Optional[int] = Field(None, ge=0, le=130)
    date_of_birth: Optional[str] = Field(None, max_length=32)
    gender: Optional[str] = Field(None, max_length=32)
    contact_number: Optional[str] = Field(None, max_length=32)
    email: Optional[str] = Field(None, max_length=255)
    medical_history: Optional[str] = Field(None, max_length=5000)
    dental_history: Optional[str] = Field(None, max_length=5000)
    notes: Optional[str] = Field(None, max_length=2000)

class PatientResponse(PatientBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    analyses_count: int = 0

    class Config:
        from_attributes = True

class TopPredictionItem(BaseModel):
    rank: int
    class_name: str
    display_name: str
    score: float
    percentage: float

class ImageAnalysisView(BaseModel):
    view: str
    label: str
    predicted_class: str
    model_output_score: float = 0.0
    confidence: Optional[float] = None  # Backwards compatibility alias
    confidence_percentage: float
    is_abstaining: bool = False
    is_inconclusive: Optional[bool] = False  # Backwards compatibility alias
    processing_status: str = "success"
    inference_time_ms: float = 0.0
    top_three_predictions: List[TopPredictionItem] = []
    model_output_scores: Dict[str, float] = {}
    original_image: Optional[str] = None
    heatmap_image: Optional[str] = None
    annotated_image: Optional[str] = None  # Backwards compatibility alias
    bounding_boxes: List[Dict[str, Any]] = []
    gradcam_salience_stats: Dict[str, Any] = {}
    gradcam_explanation: Optional[str] = None

class SingleImageAnalysisResponse(BaseModel):
    view: str
    predicted_class: str
    predicted_name: str
    model_output_score: float
    confidence_percentage: float
    is_abstaining: bool
    abstention_threshold: float
    processing_status: str
    inference_time_ms: float
    top_three_predictions: List[TopPredictionItem]
    model_output_scores: Dict[str, float]
    original_image: Optional[str] = None
    heatmap_image: Optional[str] = None
    gradcam_salience_stats: Dict[str, Any] = {}
    gradcam_explanation: str
    category: Optional[str] = None
    clinical_signs: List[str] = []
    clinical_relevance: Optional[str] = None
    primary_safety_notice: str

class ConditionDetectedItem(BaseModel):
    disease_key: str
    disease_name: str
    category: Optional[str] = None
    affected_views: List[str]
    scores_by_view: Dict[str, float] = {}
    peak_score: float
    clinical_signs: List[str] = []
    clinical_relevance: Optional[str] = None
    # Backwards compatibility fields
    severity: Optional[str] = "Moderate"
    view_count: Optional[int] = 1
    peak_confidence: Optional[float] = 0.0
    calibrated_confidence: Optional[float] = 0.0
    confidence_percentage: Optional[float] = 0.0
    confidences_by_view: Optional[Dict[str, float]] = {}
    recommendations: Optional[List[str]] = []

class ScreeningSummary(BaseModel):
    overall_status: str
    triage_recommendation: Optional[str] = "Clinical Review Required"
    urgency_level: Optional[str] = "Routine"  # Backwards compatibility
    narrative: str
    abstained_views: List[str] = []
    inconclusive_views: Optional[List[str]] = []  # Backwards compatibility
    has_abstained_views: bool = False
    requires_repeat_scans: Optional[bool] = False
    multi_view_notice: Optional[str] = None

class ReportDetailResponse(BaseModel):
    report_id: str
    scan_date: str
    scan_date_iso: str
    total_inference_time_ms: Optional[float] = 0.0
    patient: Dict[str, Any]
    screening_summary: ScreeningSummary
    conditions_detected: Optional[List[ConditionDetectedItem]] = []
    detected_conditions: Optional[List[Any]] = []  # Backwards compatibility
    images_analyzed: List[ImageAnalysisView]
    recommended_examination_steps: Optional[List[str]] = []
    clinical_recommendations: Optional[List[str]] = []  # Backwards compatibility
    primary_safety_notice: Optional[str] = None
    disclaimer: str

class AnalysisSummaryResponse(BaseModel):
    analysis_id: str
    report_id: str
    patient_id: str
    patient_name: str
    overall_status: str
    urgency_level: str
    created_at: datetime
    findings_count: int

class DashboardStats(BaseModel):
    total_patients: int
    total_scans: int
    completed_scans: int = 0
    inconclusive_scans: int = 0
    disease_distribution: Dict[str, int]
    urgency_distribution: Dict[str, int]
    recent_analyses: List[AnalysisSummaryResponse]
    scans_over_time: List[Dict[str, Any]] = []

class HealthStatus(BaseModel):
    status: str
    ai_model_loaded: bool
    database_status: str
    database_type: str
    supported_classes: List[str]
    timestamp: str

class ModelStatusResponse(BaseModel):
    is_loaded: bool
    file_exists: bool
    model_path: str
    architecture: str
    input_shape: List[Optional[int]]
    output_shape: List[Optional[int]]
    num_classes: int
    classes: List[str]
    class_mapping: Dict[int, str]
    gradcam_layer: str
    abstention_threshold: float
    model_size_mb: float
    primary_safety_notice: str
    timestamp: str
