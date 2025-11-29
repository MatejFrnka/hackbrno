"""
Medical inconsistency detection.

Uses LLM to identify contradictions, temporal impossibilities, and unlikely changes
in medical data across patient records.
"""

from typing import List
from openai import OpenAI
from pydantic import BaseModel
from .models import (
    PatientExtractionResult,
    PatientData,
    InconsistencyDetection
)
from .prompts import INCONSISTENCY_DETECTION_SYSTEM_PROMPT


class InconsistencyDetector:
    """Detect medical inconsistencies in extracted data"""

    def __init__(self, client: OpenAI, model: str = "gpt-4o-2024-08-06"):
        """
        Initialize inconsistency detector.

        Args:
            client: OpenAI client instance
            model: Model to use for detection
        """
        self.client = client
        self.model = model

    def detect(self,
               extractions: PatientExtractionResult,
               patient_data: PatientData) -> List[InconsistencyDetection]:
        """
        Detect inconsistencies in patient extractions.

        Args:
            extractions: All patient extractions with spans
            patient_data: Original patient data for context

        Returns:
            List of detected inconsistencies
        """
        print("Detecting medical inconsistencies...")

        # Prepare data summary for LLM
        data_summary = self._create_data_summary(extractions, patient_data)

        # Create prompt
        user_message = f"""Patient ID: {patient_data.patient_id}

Extracted medical information:

{data_summary}

Analyze this data for medical inconsistencies, contradictions, temporal impossibilities,
unlikely changes, and missing expected information.
"""

        try:
            # Define response model
            class InconsistencyResponse(BaseModel):
                inconsistencies: List[InconsistencyDetection]

            # Call LLM
            response = self.client.beta.chat.completions.parse(
                model=self.model,
                messages=[
                    {"role": "system", "content": INCONSISTENCY_DETECTION_SYSTEM_PROMPT},
                    {"role": "user", "content": user_message}
                ],
                response_format=InconsistencyResponse
            )

            inconsistencies = response.choices[0].message.parsed.inconsistencies

            if inconsistencies:
                print(f"✓ Found {len(inconsistencies)} inconsistencies:")
                for inc in inconsistencies:
                    print(f"  - [{inc.severity}] {inc.inconsistency_type}: {inc.description[:80]}...")
            else:
                print("✓ No inconsistencies found")

            return inconsistencies

        except Exception as e:
            print(f"ERROR: Inconsistency detection failed: {e}")
            return []

    def _create_data_summary(self,
                            extractions: PatientExtractionResult,
                            patient_data: PatientData) -> str:
        """
        Create a comprehensive summary of patient data for inconsistency analysis.

        Args:
            extractions: Patient extractions
            patient_data: Original patient data

        Returns:
            Text summary
        """
        lines = []

        # Timeline of records
        lines.append("RECORD TIMELINE:")
        for record in patient_data.records:
            lines.append(f"  {record.date} ({record.record_type}): {record.record_id}")
        lines.append("")

        # Diagnosis dates
        if extractions.diagnosis_dates:
            lines.append("DIAGNOSIS DATES:")
            for idx, dx in enumerate(extractions.diagnosis_dates):
                lines.append(f"  [{idx}] {dx.date_value} (inferred: {dx.inferred})")
                if dx.notes:
                    lines.append(f"      Note: {dx.notes}")
            lines.append("")

        # TNM classifications
        if extractions.tnm_classifications:
            lines.append("TNM CLASSIFICATIONS:")
            for idx, tnm in enumerate(extractions.tnm_classifications):
                record_ids = set(s.record_id for s in tnm.spans)
                lines.append(f"  [{idx}] {tnm.tnm_value} ({tnm.classification_type}) - Records: {', '.join(record_ids)}")
            lines.append("")

        # Hormone receptors
        if extractions.hormone_receptors:
            lines.append("HORMONE RECEPTORS:")
            for idx, receptor in enumerate(extractions.hormone_receptors):
                record_ids = set(s.record_id for s in receptor.spans)
                lines.append(f"  [{idx}] {receptor.receptor_type}: {receptor.value} - Records: {', '.join(record_ids)}")
            lines.append("")

        # External treatments
        if extractions.external_treatments:
            lines.append("EXTERNAL TREATMENTS:")
            for idx, treatment in enumerate(extractions.external_treatments):
                lines.append(f"  [{idx}] {treatment.treatment_description[:100]} ({treatment.location or 'unknown location'})")
            lines.append("")

        # Progressions
        if extractions.progressions:
            lines.append("PROGRESSIONS:")
            for idx, prog in enumerate(extractions.progressions):
                lines.append(f"  [{idx}] {prog.progression_type[:100]} (Date: {prog.date_mentioned or 'unknown'})")
            lines.append("")

        # Recurrences
        if extractions.recurrences:
            lines.append("RECURRENCES:")
            for idx, rec in enumerate(extractions.recurrences):
                lines.append(f"  [{idx}] {rec.recurrence_type[:100]} (Date: {rec.date_mentioned or 'unknown'})")
            lines.append("")

        # Metastases
        if extractions.metastases:
            lines.append("METASTASES:")
            for idx, met in enumerate(extractions.metastases):
                lines.append(f"  [{idx}] {met.location} (Date: {met.date_mentioned or 'unknown'})")
            lines.append("")

        return "\n".join(lines)
