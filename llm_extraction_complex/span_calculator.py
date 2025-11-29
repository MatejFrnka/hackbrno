"""
Span calculator for converting text citations to character positions.

Takes LLM-extracted text citations and deterministically finds their positions
in the original medical records using exact and fuzzy matching.
"""

import re
from typing import List, Optional, Dict, Tuple
from difflib import SequenceMatcher
from .models import (
    TextCitation, TextSpan, MedicalRecord,
    DiagnosisDateExtraction, TNMClassification, HormoneReceptorExtraction,
    ExternalTreatmentExtraction, ProgressionExtraction, RecurrenceExtraction,
    MetastasesExtraction,
    DiagnosisDateExtractionWithSpans, TNMClassificationWithSpans,
    HormoneReceptorExtractionWithSpans, ExternalTreatmentExtractionWithSpans,
    ProgressionExtractionWithSpans, RecurrenceExtractionWithSpans,
    MetastasesExtractionWithSpans,
    SingleRecordExtractionResult, PatientExtractionResult, PatientData
)


class SpanCalculator:
    """Calculate character spans for LLM-extracted text citations"""

    def __init__(self, fuzzy_threshold: float = 0.9):
        """
        Initialize span calculator.

        Args:
            fuzzy_threshold: Minimum similarity ratio for fuzzy matching (0.0-1.0)
        """
        self.fuzzy_threshold = fuzzy_threshold

    def find_spans(self, citation: TextCitation, record: MedicalRecord) -> List[TextSpan]:
        """
        Find all occurrences of citation text in the record.

        Args:
            citation: Text citation from LLM
            record: Medical record to search in

        Returns:
            List of TextSpan objects with calculated positions.
            If text appears multiple times, returns all occurrences.
            Returns empty list if no match found.
        """
        # Handle empty citation
        if not citation.text.strip():
            print(f"Warning: Empty citation in record {record.record_id}")
            return []

        # Normalize texts for matching
        normalized_citation = self._normalize_whitespace(citation.text)
        record_text = record.text

        # Find all occurrences
        spans = []
        start = 0
        match_index = 0

        while start < len(record_text):
            # Try exact match first (case-insensitive)
            pos = record_text.lower().find(normalized_citation.lower(), start)

            if pos != -1:
                # Exact match found
                end = pos + len(normalized_citation)

                spans.append(TextSpan(
                    text=record_text[pos:end],  # Preserve original casing
                    start_char=pos,
                    end_char=end,
                    record_id=record.record_id,
                    confidence=citation.confidence,
                    match_index=match_index
                ))

                start = end
                match_index += 1

            else:
                # Try fuzzy match if no exact match
                fuzzy_result = self._fuzzy_find(
                    normalized_citation,
                    record_text[start:],
                    threshold=self.fuzzy_threshold
                )

                if fuzzy_result:
                    pos = start + fuzzy_result['start']
                    end = start + fuzzy_result['end']

                    print(f"Fuzzy match (similarity: {fuzzy_result['similarity']:.2f}) "
                          f"in {record.record_id}: '{citation.text[:50]}...'")

                    spans.append(TextSpan(
                        text=record_text[pos:end],
                        start_char=pos,
                        end_char=end,
                        record_id=record.record_id,
                        confidence="low" if citation.confidence == "high" else citation.confidence,
                        match_index=match_index
                    ))

                    start = end
                    match_index += 1
                else:
                    # No match found at all
                    break

        if not spans:
            print(f"Warning: No match found for citation in {record.record_id}: '{citation.text[:100]}'")

        return spans

    def _normalize_whitespace(self, text: str) -> str:
        """
        Normalize whitespace in text.

        Collapses multiple whitespace characters into single space,
        trims leading/trailing whitespace.

        Args:
            text: Input text

        Returns:
            Normalized text
        """
        return re.sub(r'\s+', ' ', text).strip()

    def _fuzzy_find(self,
                    pattern: str,
                    text: str,
                    threshold: float = 0.9) -> Optional[Dict[str, any]]:
        """
        Find approximate match using sliding window.

        Args:
            pattern: Text pattern to find
            text: Text to search in
            threshold: Minimum similarity ratio (0.0-1.0)

        Returns:
            Dict with 'start', 'end', 'similarity' if match found, else None
        """
        pattern_len = len(pattern)

        # Don't fuzzy match very short patterns
        if pattern_len < 10:
            return None

        best_match = None
        best_ratio = 0

        # Sliding window search
        for i in range(len(text) - pattern_len + 1):
            window = text[i:i + pattern_len]
            ratio = SequenceMatcher(None, pattern.lower(), window.lower()).ratio()

            if ratio > best_ratio and ratio >= threshold:
                best_ratio = ratio
                best_match = {
                    'start': i,
                    'end': i + pattern_len,
                    'similarity': ratio
                }

        return best_match

    def calculate_all_spans(self,
                           extractions: List[SingleRecordExtractionResult],
                           patient_data: PatientData) -> PatientExtractionResult:
        """
        Calculate spans for all extractions from all records.

        Args:
            extractions: List of extraction results (one per record)
            patient_data: Patient data containing all records

        Returns:
            PatientExtractionResult with all spans calculated
        """
        # Create record lookup
        record_map = {r.record_id: r for r in patient_data.records}

        # Initialize result containers
        all_diagnosis_dates = []
        all_tnm = []
        all_receptors = []
        all_external_treatments = []
        all_progressions = []
        all_recurrences = []
        all_metastases = []

        # Process each record's extractions
        for record_result in extractions:
            record = record_map.get(record_result.record_id)
            if not record:
                print(f"Warning: Record {record_result.record_id} not found in patient data")
                continue

            # Process diagnosis dates
            for dx_date in record_result.diagnosis_dates:
                spans = []
                for citation in dx_date.citations:
                    spans.extend(self.find_spans(citation, record))

                all_diagnosis_dates.append(DiagnosisDateExtractionWithSpans(
                    date_value=dx_date.date_value,
                    spans=spans,
                    inferred=dx_date.inferred,
                    notes=dx_date.notes
                ))

            # Process TNM classifications
            for tnm in record_result.tnm_classifications:
                spans = []
                for citation in tnm.citations:
                    spans.extend(self.find_spans(citation, record))

                all_tnm.append(TNMClassificationWithSpans(
                    classification_type=tnm.classification_type,
                    tnm_value=tnm.tnm_value,
                    spans=spans
                ))

            # Process hormone receptors
            for receptor in record_result.hormone_receptors:
                spans = []
                for citation in receptor.citations:
                    spans.extend(self.find_spans(citation, record))

                all_receptors.append(HormoneReceptorExtractionWithSpans(
                    receptor_type=receptor.receptor_type,
                    value=receptor.value,
                    spans=spans
                ))

            # Process external treatments
            for treatment in record_result.external_treatments:
                spans = []
                for citation in treatment.citations:
                    spans.extend(self.find_spans(citation, record))

                all_external_treatments.append(ExternalTreatmentExtractionWithSpans(
                    treatment_description=treatment.treatment_description,
                    location=treatment.location,
                    spans=spans
                ))

            # Process progressions
            for progression in record_result.progressions:
                spans = []
                for citation in progression.citations:
                    spans.extend(self.find_spans(citation, record))

                all_progressions.append(ProgressionExtractionWithSpans(
                    progression_type=progression.progression_type,
                    date_mentioned=progression.date_mentioned,
                    spans=spans
                ))

            # Process recurrences
            for recurrence in record_result.recurrences:
                spans = []
                for citation in recurrence.citations:
                    spans.extend(self.find_spans(citation, record))

                all_recurrences.append(RecurrenceExtractionWithSpans(
                    recurrence_type=recurrence.recurrence_type,
                    date_mentioned=recurrence.date_mentioned,
                    spans=spans
                ))

            # Process metastases
            for metastasis in record_result.metastases:
                spans = []
                for citation in metastasis.citations:
                    spans.extend(self.find_spans(citation, record))

                all_metastases.append(MetastasesExtractionWithSpans(
                    location=metastasis.location,
                    date_mentioned=metastasis.date_mentioned,
                    spans=spans
                ))

        return PatientExtractionResult(
            patient_id=patient_data.patient_id,
            diagnosis_dates=all_diagnosis_dates,
            tnm_classifications=all_tnm,
            hormone_receptors=all_receptors,
            external_treatments=all_external_treatments,
            progressions=all_progressions,
            recurrences=all_recurrences,
            metastases=all_metastases
        )
