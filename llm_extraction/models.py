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


@dataclass
class MedicalRecord:
    """Single medical record from XML"""
    record_id: int               # integer for now
    patient_id: str              # Patient identifier eg "HACK01"
    date: str                    # YYYY-MM-DD
    record_type: str             # "typ" field from XML
    text: str                    # Full record text
    text_hash: str               # SHA256 for dedup


@dataclass
class PatientData:
    """Complete patient data from XML"""
    patient_id: str
    records: List[MedicalRecord]


@dataclass
class Question:
    """Extraction question definition"""
    question_id: int
    text: str
    additional_instructions: Optional[str] = None


class ExtractionCitation(BaseModel):
    """Citation used in extraction results"""
    question_id: int                                # ID of the question this citation answers
    quoted_text: str                                # Exact quoted text from record
    confidence: Literal["high", "medium", "low"]    # Confidence level


class ExtractionCitationWithSpan(BaseModel):
    """Text span within a medical record"""
    question_id: int                                # ID of the question this citation answers
    quoted_text: str                                # Exact quoted text from record
    confidence: Literal["high", "medium", "low"]    # Confidence level
    record_id: int                                  # ID of the medical record
    start_char: int                                 # Start character index in record text
    end_char: int                                   # End character index in record text
