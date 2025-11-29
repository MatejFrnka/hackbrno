"""
Utility functions for the extraction pipeline.
"""

from typing import List
from .models import PatientData


def estimate_tokens(patient_data: PatientData) -> int:
    """
    Estimate token count for patient data.

    Uses rough estimation: 1 token ≈ 4 characters for Czech text.

    Args:
        patient_data: Patient data to estimate

    Returns:
        Estimated token count
    """
    total_chars = sum(len(record.text) for record in patient_data.records)
    # Add overhead for metadata (dates, types, delimiters)
    overhead = len(patient_data.records) * 50
    total_chars += overhead

    # Rough estimate: 1 token ≈ 4 characters
    return total_chars // 4


def estimate_tokens_for_text(text: str) -> int:
    """
    Estimate token count for a text string.

    Args:
        text: Text to estimate

    Returns:
        Estimated token count
    """
    return len(text) // 4
