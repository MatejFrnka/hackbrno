"""
Semantic deduplication for medical extractions.

Uses LLM to identify semantically identical extractions that may be worded differently.
"""

from typing import List
from openai import OpenAI
from pydantic import BaseModel
from .models import (
    PatientExtractionResult,
    DeduplicationResult,
    SemanticDuplicateGroup
)
from .prompts import DEDUPLICATION_SYSTEM_PROMPT


class SemanticDeduplicator:
    """Identify and group semantically duplicate extractions"""

    def __init__(self, client: OpenAI, model: str = "gpt-4o-2024-08-06"):
        """
        Initialize deduplicator.

        Args:
            client: OpenAI client instance
            model: Model to use for deduplication
        """
        self.client = client
        self.model = model

    def deduplicate_extractions(self, extractions: PatientExtractionResult) -> DeduplicationResult:
        """
        Find semantic duplicates across all extraction types.

        Args:
            extractions: Patient extractions with spans

        Returns:
            DeduplicationResult with duplicate groups for each feature type
        """
        print("Performing semantic deduplication...")

        result = DeduplicationResult()

        # Deduplicate each feature type
        result.diagnosis_date_duplicates = self._deduplicate_feature(
            extractions.diagnosis_dates,
            "diagnosis dates"
        )

        result.tnm_duplicates = self._deduplicate_feature(
            extractions.tnm_classifications,
            "TNM classifications"
        )

        result.receptor_duplicates = self._deduplicate_feature(
            extractions.hormone_receptors,
            "hormone receptors"
        )

        result.external_treatment_duplicates = self._deduplicate_feature(
            extractions.external_treatments,
            "external treatments"
        )

        result.progression_duplicates = self._deduplicate_feature(
            extractions.progressions,
            "progressions"
        )

        result.recurrence_duplicates = self._deduplicate_feature(
            extractions.recurrences,
            "recurrences"
        )

        result.metastases_duplicates = self._deduplicate_feature(
            extractions.metastases,
            "metastases"
        )

        # Count total duplicates found
        total_groups = (
            len(result.diagnosis_date_duplicates) +
            len(result.tnm_duplicates) +
            len(result.receptor_duplicates) +
            len(result.external_treatment_duplicates) +
            len(result.progression_duplicates) +
            len(result.recurrence_duplicates) +
            len(result.metastases_duplicates)
        )
        print(f"✓ Found {total_groups} duplicate groups")

        return result

    def _deduplicate_feature(self, extractions: List, feature_name: str) -> List[SemanticDuplicateGroup]:
        """
        Find semantic duplicates within a single feature type.

        Args:
            extractions: List of extractions (all same type)
            feature_name: Name of feature for logging

        Returns:
            List of duplicate groups
        """
        if len(extractions) < 2:
            print(f"  - {feature_name}: {len(extractions)} items (skipping dedup)")
            return []

        print(f"  - {feature_name}: Checking {len(extractions)} items...")

        # Prepare extraction summaries for LLM
        summaries = []
        for idx, extraction in enumerate(extractions):
            # Create summary based on type
            summary = self._create_summary(extraction, idx)
            summaries.append(summary)

        # Create prompt for LLM
        user_message = f"""Feature type: {feature_name}

Extractions to analyze:

{chr(10).join(summaries)}

Identify semantic duplicates among these extractions. Return groups of duplicates.
"""

        try:
            # Define response model
            class DeduplicationResponse(BaseModel):
                duplicate_groups: List[SemanticDuplicateGroup]

            # Call LLM
            response = self.client.beta.chat.completions.parse(
                model=self.model,
                messages=[
                    {"role": "system", "content": DEDUPLICATION_SYSTEM_PROMPT},
                    {"role": "user", "content": user_message}
                ],
                response_format=DeduplicationResponse
            )

            groups = response.choices[0].message.parsed.duplicate_groups

            if groups:
                print(f"    → Found {len(groups)} duplicate groups")
            else:
                print(f"    → No duplicates found")

            return groups

        except Exception as e:
            print(f"    ERROR: Deduplication failed: {e}")
            return []

    def _create_summary(self, extraction, idx: int) -> str:
        """
        Create a text summary of an extraction for LLM analysis.

        Args:
            extraction: Extraction object (any type)
            idx: Index of this extraction

        Returns:
            Text summary
        """
        # Handle different extraction types
        if hasattr(extraction, 'date_value'):
            # DiagnosisDateExtractionWithSpans
            spans_text = ", ".join([s.text[:50] for s in extraction.spans[:2]])
            return f"[{idx}] Date: {extraction.date_value}, Spans: {spans_text}"

        elif hasattr(extraction, 'tnm_value'):
            # TNMClassificationWithSpans
            spans_text = ", ".join([s.text[:50] for s in extraction.spans[:2]])
            return f"[{idx}] TNM: {extraction.tnm_value} ({extraction.classification_type}), Spans: {spans_text}"

        elif hasattr(extraction, 'receptor_type'):
            # HormoneReceptorExtractionWithSpans
            spans_text = ", ".join([s.text[:50] for s in extraction.spans[:2]])
            return f"[{idx}] {extraction.receptor_type}: {extraction.value}, Spans: {spans_text}"

        elif hasattr(extraction, 'treatment_description'):
            # ExternalTreatmentExtractionWithSpans
            return f"[{idx}] Treatment: {extraction.treatment_description[:100]}, Location: {extraction.location or 'unknown'}"

        elif hasattr(extraction, 'progression_type'):
            # ProgressionExtractionWithSpans
            return f"[{idx}] Progression: {extraction.progression_type[:100]}, Date: {extraction.date_mentioned or 'unknown'}"

        elif hasattr(extraction, 'recurrence_type'):
            # RecurrenceExtractionWithSpans
            return f"[{idx}] Recurrence: {extraction.recurrence_type[:100]}, Date: {extraction.date_mentioned or 'unknown'}"

        elif hasattr(extraction, 'location'):
            # MetastasesExtractionWithSpans
            return f"[{idx}] Metastases: {extraction.location}, Date: {extraction.date_mentioned or 'unknown'}"

        else:
            return f"[{idx}] {str(extraction)[:100]}"
