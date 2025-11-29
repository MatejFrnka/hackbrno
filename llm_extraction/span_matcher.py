"""
Span matching for citations - maps extracted text to character positions.

Uses whitespace normalization, lowercase matching, and Levenshtein distance
to find first occurrence of citations in source text.
"""

from typing import Optional, List
import re
from difflib import SequenceMatcher

from llm_extraction.models import (
    ExtractionCitation,
    ExtractionCitationWithSpan,
    HighlightCitation,
    HighlightCitationWithSpan,
    MedicalRecord,
    PatientData
)


class SpanMatcher:
    """Match citations to exact character positions in source text"""

    def __init__(self, similarity_threshold: float = 0.9):
        """
        Args:
            similarity_threshold: Minimum Levenshtein similarity (0.0-1.0)
        """
        self.similarity_threshold = similarity_threshold

    def normalize_whitespace(self, text: str) -> str:
        """
        Normalize whitespace: collapse multiple spaces/tabs/newlines to single space.

        Examples:
            "ER  100%" → "ER 100%"
            "cT2N0M0\n" → "cT2N0M0"

        Args:
            text: Input text

        Returns:
            Text with normalized whitespace
        """
        return re.sub(r'\s+', ' ', text).strip()

    def find_first_match(
        self,
        citation: ExtractionCitation,
        record: MedicalRecord
    ) -> Optional[ExtractionCitationWithSpan]:
        """
        Find first occurrence of citation text in record.

        Process:
        1. Normalize both citation and record text (whitespace)
        2. Convert to lowercase
        3. Try exact match first
        4. If no exact match, use sliding window with Levenshtein distance
        5. Return first match found (or None)

        Args:
            citation: Extracted citation from LLM
            record: Source medical record

        Returns:
            ExtractionCitationWithSpan with calculated positions, or None if no match
        """
        # Step 1: Normalize whitespace
        normalized_citation = self.normalize_whitespace(citation.quoted_text)
        normalized_record = self.normalize_whitespace(record.text)

        # Step 2: Convert to lowercase
        citation_lower = normalized_citation.lower()
        record_lower = normalized_record.lower()

        # Step 3: Try exact match first
        pos = record_lower.find(citation_lower)

        if pos != -1:
            # Exact match found
            end_pos = pos + len(citation_lower)

            # Map back to original text positions
            original_start, original_end = self._map_to_original_positions(
                original_text=record.text,
                normalized_text=normalized_record,
                norm_start=pos,
                norm_end=end_pos
            )

            # Check for invalid span (both start and end are 0)
            if original_start == 0 and original_end == 0:
                print(f"WARNING: Invalid span (start=0, end=0) for citation: '{citation.quoted_text}' in record {record.record_id}")
                return None

            return ExtractionCitationWithSpan(
                question_id=citation.question_id,
                quoted_text=citation.quoted_text,
                confidence=citation.confidence,
                record_id=record.record_id,
                start_char=original_start,
                end_char=original_end
            )

        # Step 4: No exact match - try fuzzy matching
        fuzzy_match = self._fuzzy_find_first(
            pattern=citation_lower,
            text=record_lower,
            threshold=self.similarity_threshold
        )

        if fuzzy_match:
            # Map back to original positions
            original_start, original_end = self._map_to_original_positions(
                original_text=record.text,
                normalized_text=normalized_record,
                norm_start=fuzzy_match['start'],
                norm_end=fuzzy_match['end']
            )

            # Check for invalid span (both start and end are 0)
            if original_start == 0 and original_end == 0:
                print(f"WARNING: Invalid span (start=0, end=0) for citation: '{citation.quoted_text}' in record {record.record_id}")
                return None

            return ExtractionCitationWithSpan(
                question_id=citation.question_id,
                quoted_text=citation.quoted_text,
                confidence=citation.confidence,
                record_id=record.record_id,
                start_char=original_start,
                end_char=original_end
            )

        # No match found
        print(f"WARNING: No match found for citation: '{citation.quoted_text}' in record {record.record_id}")
        return None

    def _fuzzy_find_first(
        self,
        pattern: str,
        text: str,
        threshold: float
    ) -> Optional[dict]:
        """
        Find first approximate match using sliding window + Levenshtein distance.

        Args:
            pattern: Citation text (normalized, lowercase)
            text: Record text (normalized, lowercase)
            threshold: Minimum similarity ratio (0.0-1.0)

        Returns:
            {'start': int, 'end': int, 'similarity': float} or None
        """
        pattern_len = len(pattern)

        # Sliding window search
        for i in range(len(text) - pattern_len + 1):
            window = text[i:i + pattern_len]

            # Calculate Levenshtein similarity
            ratio = SequenceMatcher(None, pattern, window).ratio()

            if ratio >= threshold:
                # First match found - return immediately
                return {
                    'start': i,
                    'end': i + pattern_len,
                    'similarity': ratio
                }

        # No match found
        return None

    def _map_to_original_positions(
        self,
        original_text: str,
        normalized_text: str,
        norm_start: int,
        norm_end: int
    ) -> tuple:
        """
        Map positions from normalized text back to original text.

        Since normalization only collapses whitespace, we need to find
        where the normalized span maps in the original text.

        Strategy:
        1. Build mapping of normalized char index → original char index
        2. Lookup norm_start and norm_end in mapping

        Args:
            original_text: Source text before normalization
            normalized_text: Text after whitespace normalization
            norm_start: Start position in normalized text
            norm_end: End position in normalized text

        Returns:
            (original_start, original_end)
        """
        # Build mapping: normalized_index → original_index
        norm_to_orig = []

        # Track whitespace runs
        in_whitespace = False

        for orig_idx, char in enumerate(original_text):
            if char.isspace():
                if not in_whitespace:
                    # First whitespace char → maps to space in normalized
                    norm_to_orig.append(orig_idx)
                    in_whitespace = True
                # Subsequent whitespace chars don't map (collapsed)
            else:
                # Non-whitespace char
                norm_to_orig.append(orig_idx)
                in_whitespace = False

        # Add final position
        norm_to_orig.append(len(original_text))

        # Look up positions
        if norm_start >= len(norm_to_orig):
            print(f"WARNING: norm_start {norm_start} out of bounds")
            norm_start = len(norm_to_orig) - 1

        if norm_end >= len(norm_to_orig):
            print(f"WARNING: norm_end {norm_end} out of bounds")
            norm_end = len(norm_to_orig) - 1

        original_start = norm_to_orig[norm_start]
        original_end = norm_to_orig[norm_end]

        return (original_start, original_end)

    def match_all_citations(
        self,
        extraction_results: List[dict],
        patient_data: PatientData
    ) -> List[ExtractionCitationWithSpan]:
        """
        Match all citations to their source positions.

        Args:
            extraction_results: List of {'record_id': str, 'citations': List[ExtractionCitation]}
            patient_data: Patient data with records

        Returns:
            List of ExtractionCitationWithSpan (only successful matches)
        """
        all_spans = []

        print(f"Matching citations to source text positions...")

        for result in extraction_results:
            record_id = result['record_id']
            citations = result['citations']

            # Find corresponding record
            record = None
            for r in patient_data.records:
                if r.record_id == record_id:
                    record = r
                    break

            if not record:
                print(f"WARNING: Record {record_id} not found")
                continue

            # Match each citation
            for citation in citations:
                span = self.find_first_match(citation, record)
                if span:
                    all_spans.append(span)

        print(f"  → Matched {len(all_spans)} citations successfully")

        return all_spans

    def match_highlight_citations(
        self,
        highlight_results: List[dict],
        patient_data: PatientData
    ) -> List[HighlightCitationWithSpan]:
        """
        Match highlight citations to their source positions.

        Args:
            highlight_results: List of {
                'record_id': int,
                'record_date': str,
                'record_type': str,
                'highlights': List[HighlightCitation]
            }
            patient_data: Patient data with records

        Returns:
            List of HighlightCitationWithSpan (only successful matches)
        """
        all_spans = []

        print(f"Matching highlight citations to source text positions...")

        for result in highlight_results:
            record_id = result['record_id']
            highlights = result['highlights']

            # Find corresponding record
            record = None
            for r in patient_data.records:
                if r.record_id == record_id:
                    record = r
                    break

            if not record:
                print(f"WARNING: Record {record_id} not found")
                continue

            # Match each highlight
            for highlight in highlights:
                # Create temporary ExtractionCitation for compatibility with find_first_match
                temp_citation = ExtractionCitation(
                    question_id=0,  # Not used for highlights
                    quoted_text=highlight.quoted_text,
                    confidence="high"  # Not used for highlights
                )

                span = self.find_first_match(temp_citation, record)

                if span:
                    # Convert to HighlightCitationWithSpan
                    highlight_span = HighlightCitationWithSpan(
                        quoted_text=highlight.quoted_text,
                        note=highlight.note,
                        record_id=record_id,
                        start_char=span.start_char,
                        end_char=span.end_char
                    )
                    all_spans.append(highlight_span)

        print(f"  → Matched {len(all_spans)} highlight citations successfully")

        return all_spans
