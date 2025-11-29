"""
Pydantic models for medical information extraction pipeline.

Defines data structures for:
- Text citations and spans
- Feature extractions (with and without spans)
- Quality control (deduplication, inconsistencies)
- Timeline generation
"""

from typing import List, Optional, Literal
from pydantic import BaseModel
from dataclasses import dataclass


# ============================================================================
# Core Text Models
# ============================================================================

class TextCitation(BaseModel):
    """LLM-extracted citation (no positions yet)"""
    text: str                    # Exact quoted text from record
    confidence: Literal["high", "medium", "low"]


class TextSpan(BaseModel):
    """Citation with calculated character positions"""
    text: str                    # Exact extracted text
    start_char: int              # Character index in source record
    end_char: int                # Exclusive end
    record_id: str               # Source record ID
    confidence: Literal["high", "medium", "low"]
    match_index: int = 0         # Which occurrence if text appears multiple times


# ============================================================================
# LLM Extraction Models (Citations Only)
# ============================================================================

class DiagnosisDateExtraction(BaseModel):
    """Date when diagnosis was established"""
    date_value: Optional[str] = None    # YYYY-MM-DD or null
    citations: List[TextCitation] = []  # LLM returns these
    record_id: str                      # Which record this came from
    inferred: bool = False              # Was date inferred from context?
    notes: Optional[str] = None         # Additional context


class TNMClassification(BaseModel):
    """TNM tumor classification (clinical or pathological)"""
    classification_type: Literal["clinical", "pathological", "unknown"]
    tnm_value: str                      # e.g., "cT2N0M0" or "pT2 pN0(i−)(sn) M0"
    citations: List[TextCitation] = []
    record_id: str


class HormoneReceptorExtraction(BaseModel):
    """Hormone receptor test results (ER, PR, HER2)"""
    receptor_type: Literal["ER", "PR", "HER2"]
    value: str                          # "100%", "10%", "negative", "0", etc.
    citations: List[TextCitation] = []
    record_id: str


class ExternalTreatmentExtraction(BaseModel):
    """Treatment received outside MOÚ hospital"""
    treatment_description: str
    location: Optional[str] = None      # Hospital/facility name
    citations: List[TextCitation] = []
    record_id: str


class ProgressionExtraction(BaseModel):
    """Disease progression information"""
    progression_type: str                # Description of progression
    date_mentioned: Optional[str] = None # When progression was noted
    citations: List[TextCitation] = []
    record_id: str


class RecurrenceExtraction(BaseModel):
    """Disease recurrence information"""
    recurrence_type: str                # Description of recurrence
    date_mentioned: Optional[str] = None
    citations: List[TextCitation] = []
    record_id: str


class MetastasesExtraction(BaseModel):
    """Distant metastases information"""
    location: str                        # "játra", "kosti", "plíce", etc.
    date_mentioned: Optional[str] = None
    citations: List[TextCitation] = []
    record_id: str


# ============================================================================
# Post-Processed Models (With Calculated Spans)
# ============================================================================

class DiagnosisDateExtractionWithSpans(BaseModel):
    """Diagnosis date with calculated text spans"""
    date_value: Optional[str] = None
    spans: List[TextSpan] = []          # Calculated from citations
    inferred: bool = False
    notes: Optional[str] = None


class TNMClassificationWithSpans(BaseModel):
    """TNM classification with calculated text spans"""
    classification_type: Literal["clinical", "pathological", "unknown"]
    tnm_value: str
    spans: List[TextSpan] = []


class HormoneReceptorExtractionWithSpans(BaseModel):
    """Hormone receptor with calculated text spans"""
    receptor_type: Literal["ER", "PR", "HER2"]
    value: str
    spans: List[TextSpan] = []


class ExternalTreatmentExtractionWithSpans(BaseModel):
    """External treatment with calculated text spans"""
    treatment_description: str
    location: Optional[str] = None
    spans: List[TextSpan] = []


class ProgressionExtractionWithSpans(BaseModel):
    """Progression with calculated text spans"""
    progression_type: str
    date_mentioned: Optional[str] = None
    spans: List[TextSpan] = []


class RecurrenceExtractionWithSpans(BaseModel):
    """Recurrence with calculated text spans"""
    recurrence_type: str
    date_mentioned: Optional[str] = None
    spans: List[TextSpan] = []


class MetastasesExtractionWithSpans(BaseModel):
    """Metastases with calculated text spans"""
    location: str
    date_mentioned: Optional[str] = None
    spans: List[TextSpan] = []


# ============================================================================
# Extraction Result Containers
# ============================================================================

class SingleRecordExtractionResult(BaseModel):
    """Result from extracting features from one medical record"""
    record_id: str
    diagnosis_dates: List[DiagnosisDateExtraction] = []
    tnm_classifications: List[TNMClassification] = []
    hormone_receptors: List[HormoneReceptorExtraction] = []
    external_treatments: List[ExternalTreatmentExtraction] = []
    progressions: List[ProgressionExtraction] = []
    recurrences: List[RecurrenceExtraction] = []
    metastases: List[MetastasesExtraction] = []


class PatientExtractionResult(BaseModel):
    """All extractions for a patient (after span calculation)"""
    patient_id: str
    diagnosis_dates: List[DiagnosisDateExtractionWithSpans] = []
    tnm_classifications: List[TNMClassificationWithSpans] = []
    hormone_receptors: List[HormoneReceptorExtractionWithSpans] = []
    external_treatments: List[ExternalTreatmentExtractionWithSpans] = []
    progressions: List[ProgressionExtractionWithSpans] = []
    recurrences: List[RecurrenceExtractionWithSpans] = []
    metastases: List[MetastasesExtractionWithSpans] = []


# ============================================================================
# Quality Control Models
# ============================================================================

class SemanticDuplicateGroup(BaseModel):
    """Group of semantically identical extractions"""
    canonical_extraction: int           # Index to keep (most complete)
    duplicate_indices: List[int]        # Indices of duplicates
    reasoning: str                      # Explanation why these are duplicates


class InconsistencyDetection(BaseModel):
    """Medical inconsistency or contradiction detected"""
    inconsistency_type: Literal[
        "contradiction",
        "temporal_impossibility",
        "unlikely_change",
        "missing_expected"
    ]
    description: str                    # Detailed explanation
    involved_records: List[str]         # Which records contain the issue
    severity: Literal["critical", "moderate", "minor"]
    related_feature: str                # Which feature type


class DeduplicationResult(BaseModel):
    """Deduplication results for all feature types"""
    diagnosis_date_duplicates: List[SemanticDuplicateGroup] = []
    tnm_duplicates: List[SemanticDuplicateGroup] = []
    receptor_duplicates: List[SemanticDuplicateGroup] = []
    external_treatment_duplicates: List[SemanticDuplicateGroup] = []
    progression_duplicates: List[SemanticDuplicateGroup] = []
    recurrence_duplicates: List[SemanticDuplicateGroup] = []
    metastases_duplicates: List[SemanticDuplicateGroup] = []


# ============================================================================
# Timeline Models
# ============================================================================

class TimelineEvent(BaseModel):
    """Single event in a feature timeline"""
    date: str                           # YYYY-MM-DD or "unknown"
    description: str                    # Human-readable description
    significance: str                   # Why this event matters


class FeatureTimeline(BaseModel):
    """Timeline for a specific feature"""
    feature_name: str
    events: List[TimelineEvent] = []    # Chronologically sorted
    narrative: str = ""                 # LLM-generated summary


class PatientTimeline(BaseModel):
    """Complete timeline for patient"""
    diagnosis_timeline: FeatureTimeline
    tnm_timeline: FeatureTimeline
    receptor_timeline: FeatureTimeline
    treatment_timeline: FeatureTimeline
    progression_timeline: FeatureTimeline
    recurrence_timeline: FeatureTimeline
    metastases_timeline: FeatureTimeline
    overall_narrative: str = ""         # Complete patient journey


# ============================================================================
# Data Classes (not Pydantic - for internal use)
# ============================================================================

@dataclass
class MedicalRecord:
    """Single medical record from XML"""
    record_id: str               # "HACK01_0", "HACK01_1", etc.
    patient_id: str
    date: str                    # YYYY-MM-DD
    record_type: str             # "typ" field from XML
    text: str                    # Full record text
    text_hash: str               # SHA256 for dedup


@dataclass
class PatientData:
    """Complete patient data from XML"""
    patient_id: str
    records: List[MedicalRecord]
    duplicate_count: int = 0     # How many exact duplicates were removed


# ============================================================================
# Final Output Model
# ============================================================================

class ProcessingMetadata(BaseModel):
    """Metadata about the processing"""
    timestamp: str                      # ISO 8601 format
    model_used: str                     # e.g., "gpt-4o-2024-08-06"
    total_records_processed: int
    exact_duplicates_removed: int
    extraction_mode: Literal["bulk", "per_record"]


class PatientOutputJSON(BaseModel):
    """Complete output JSON for a patient"""
    patient_id: str
    processing_metadata: ProcessingMetadata
    extractions: PatientExtractionResult
    deduplication: DeduplicationResult
    inconsistencies: List[InconsistencyDetection]
    timeline: PatientTimeline
