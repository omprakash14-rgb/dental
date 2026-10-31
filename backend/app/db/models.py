import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, Boolean, Text, ForeignKey, JSON, DateTime
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()

def utcnow():
    return datetime.now(timezone.utc)

class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(String(64), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    age = Column(Integer, nullable=True)
    gender = Column(String(32), nullable=True)
    date_of_birth = Column(String(32), nullable=True)
    contact_number = Column(String(32), nullable=True)
    email = Column(String(255), nullable=True)
    medical_history = Column(Text, nullable=True)
    dental_history = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    # Relationships
    analyses = relationship("DentalAnalysis", back_populates="patient", cascade="all, delete-orphan")
    reports = relationship("GeneratedReport", back_populates="patient", cascade="all, delete-orphan")

class DentalAnalysis(Base):
    __tablename__ = "dental_analyses"

    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(String(64), unique=True, index=True, default=lambda: f"ANL-{uuid.uuid4().hex[:8].upper()}")
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    overall_status = Column(String(128), nullable=False)
    urgency_level = Column(String(64), nullable=False)
    summary = Column(Text, nullable=True)
    inconclusive_views = Column(JSON, default=list)
    created_at = Column(DateTime(timezone=True), default=utcnow)

    # Relationships
    patient = relationship("Patient", back_populates="analyses")
    images = relationship("UploadedImage", back_populates="analysis", cascade="all, delete-orphan")
    predictions = relationship("DiseasePrediction", back_populates="analysis", cascade="all, delete-orphan")
    report = relationship("GeneratedReport", back_populates="analysis", uselist=False, cascade="all, delete-orphan")

class UploadedImage(Base):
    __tablename__ = "uploaded_images"

    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(Integer, ForeignKey("dental_analyses.id"), nullable=False)
    view_name = Column(String(32), nullable=False)  # 'front', 'left', 'right'
    original_filename = Column(String(255), nullable=False)
    stored_filename = Column(String(255), nullable=False)
    annotated_filename = Column(String(255), nullable=True)
    heatmap_filename = Column(String(255), nullable=True)
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    clarity_score = Column(Float, nullable=True)
    is_inconclusive = Column(Boolean, default=False)
    bounding_boxes = Column(JSON, default=list)
    created_at = Column(DateTime(timezone=True), default=utcnow)

    # Relationships
    analysis = relationship("DentalAnalysis", back_populates="images")

class DiseasePrediction(Base):
    __tablename__ = "disease_predictions"

    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(Integer, ForeignKey("dental_analyses.id"), nullable=False)
    disease_key = Column(String(64), nullable=False)
    disease_name = Column(String(128), nullable=False)
    category = Column(String(64), nullable=True)
    severity = Column(String(32), nullable=True)
    peak_confidence = Column(Float, nullable=False)
    calibrated_confidence = Column(Float, nullable=False)
    affected_views = Column(JSON, default=list)
    clinical_signs = Column(JSON, default=list)
    recommendations = Column(JSON, default=list)

    # Relationships
    analysis = relationship("DentalAnalysis", back_populates="predictions")

class GeneratedReport(Base):
    __tablename__ = "generated_reports"

    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(String(64), unique=True, index=True, nullable=False)
    analysis_id = Column(Integer, ForeignKey("dental_analyses.id"), nullable=False)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    report_data = Column(JSON, nullable=False)  # Complete JSON screening report
    created_at = Column(DateTime(timezone=True), default=utcnow)

    # Relationships
    analysis = relationship("DentalAnalysis", back_populates="report")
    patient = relationship("Patient", back_populates="reports")

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(64), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(32), default="dentist", nullable=False)  # 'admin', 'dentist', 'staff'
    full_name = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    # Relationships
    audit_logs = relationship("AuditLog", back_populates="user")

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    username = Column(String(64), nullable=True)
    action = Column(String(64), nullable=False)  # e.g., 'PATIENT_CREATE', 'LOGIN_SUCCESS', 'SCREENING_EXECUTE'
    resource_type = Column(String(64), nullable=True)  # 'patient', 'screening', 'report', 'auth'
    resource_id = Column(String(64), nullable=True)
    ip_address = Column(String(64), nullable=True)
    status_code = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)

    # Relationships
    user = relationship("User", back_populates="audit_logs")

class TokenBlocklist(Base):
    __tablename__ = "token_blocklist"

    id = Column(Integer, primary_key=True, index=True)
    token_jti = Column(String(64), unique=True, index=True, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow)


