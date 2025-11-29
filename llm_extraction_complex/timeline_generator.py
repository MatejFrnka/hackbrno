"""
Timeline generation for patient medical history.

Creates chronological timelines for each feature type and an overall patient narrative.
"""

from typing import List
from openai import OpenAI
from pydantic import BaseModel
from .models import (
    PatientExtractionResult,
    PatientData,
    PatientTimeline,
    FeatureTimeline
)
from .prompts import TIMELINE_GENERATION_SYSTEM_PROMPT


class TimelineGenerator:
    """Generate chronological timelines and narratives"""

    def __init__(self, client: OpenAI, model: str = "gpt-4o-2024-08-06"):
        """
        Initialize timeline generator.

        Args:
            client: OpenAI client instance
            model: Model to use for generation
        """
        self.client = client
        self.model = model

    def generate(self,
                extractions: PatientExtractionResult,
                patient_data: PatientData) -> PatientTimeline:
        """
        Generate timeline for patient.

        Args:
            extractions: All patient extractions with spans
            patient_data: Original patient data for context

        Returns:
            PatientTimeline with all feature timelines and overall narrative
        """
        print("Generating timeline...")

        # Prepare data summary
        data_summary = self._create_timeline_data(extractions, patient_data)

        # Create prompt
        user_message = f"""Patient ID: {patient_data.patient_id}

Medical data to create timeline from:

{data_summary}

Create chronological timelines for each feature type and an overall patient narrative.
"""

        try:
            # Call LLM
            response = self.client.beta.chat.completions.parse(
                model=self.model,
                messages=[
                    {"role": "system", "content": TIMELINE_GENERATION_SYSTEM_PROMPT},
                    {"role": "user", "content": user_message}
                ],
                response_format=PatientTimeline
            )

            timeline = response.choices[0].message.parsed

            print(f"✓ Generated timeline:")
            print(f"  - Diagnosis: {len(timeline.diagnosis_timeline.events)} events")
            print(f"  - TNM: {len(timeline.tnm_timeline.events)} events")
            print(f"  - Receptors: {len(timeline.receptor_timeline.events)} events")
            print(f"  - Treatment: {len(timeline.treatment_timeline.events)} events")
            print(f"  - Progression: {len(timeline.progression_timeline.events)} events")
            print(f"  - Recurrence: {len(timeline.recurrence_timeline.events)} events")
            print(f"  - Metastases: {len(timeline.metastases_timeline.events)} events")
            print(f"  - Overall narrative: {len(timeline.overall_narrative)} chars")

            return timeline

        except Exception as e:
            print(f"ERROR: Timeline generation failed: {e}")
            # Return empty timeline
            return PatientTimeline(
                diagnosis_timeline=FeatureTimeline(feature_name="Diagnosis"),
                tnm_timeline=FeatureTimeline(feature_name="TNM Classification"),
                receptor_timeline=FeatureTimeline(feature_name="Hormone Receptors"),
                treatment_timeline=FeatureTimeline(feature_name="Treatment"),
                progression_timeline=FeatureTimeline(feature_name="Progression"),
                recurrence_timeline=FeatureTimeline(feature_name="Recurrence"),
                metastases_timeline=FeatureTimeline(feature_name="Metastases"),
                overall_narrative="Timeline generation failed."
            )

    def _create_timeline_data(self,
                             extractions: PatientExtractionResult,
                             patient_data: PatientData) -> str:
        """
        Create data summary for timeline generation.

        Args:
            extractions: Patient extractions
            patient_data: Original patient data

        Returns:
            Text summary with chronological information
        """
        lines = []

        # Record dates for context
        lines.append("RECORD DATES:")
        for record in patient_data.records:
            lines.append(f"  {record.date}: {record.record_type} ({record.record_id})")
        lines.append("")

        # Diagnosis dates
        lines.append("DIAGNOSIS INFORMATION:")
        for idx, dx in enumerate(extractions.diagnosis_dates):
            lines.append(f"  {dx.date_value or 'unknown date'}: {', '.join([s.text[:60] for s in dx.spans[:2]])}")
        lines.append("")

        # TNM classifications with record dates
        lines.append("TNM CLASSIFICATIONS:")
        for idx, tnm in enumerate(extractions.tnm_classifications):
            record_ids = sorted(set(s.record_id for s in tnm.spans))
            # Get dates for these records
            dates = []
            for record in patient_data.records:
                if record.record_id in record_ids:
                    dates.append(record.date)
            dates_str = ", ".join(sorted(set(dates)))
            lines.append(f"  {dates_str}: {tnm.tnm_value} ({tnm.classification_type})")
        lines.append("")

        # Hormone receptors
        lines.append("HORMONE RECEPTORS:")
        for idx, receptor in enumerate(extractions.hormone_receptors):
            record_ids = sorted(set(s.record_id for s in receptor.spans))
            dates = []
            for record in patient_data.records:
                if record.record_id in record_ids:
                    dates.append(record.date)
            dates_str = ", ".join(sorted(set(dates)))
            lines.append(f"  {dates_str}: {receptor.receptor_type} = {receptor.value}")
        lines.append("")

        # External treatments
        lines.append("EXTERNAL TREATMENTS:")
        for idx, treatment in enumerate(extractions.external_treatments):
            lines.append(f"  {treatment.treatment_description[:100]}")
        lines.append("")

        # Progressions
        lines.append("PROGRESSIONS:")
        for idx, prog in enumerate(extractions.progressions):
            date = prog.date_mentioned or "unknown date"
            lines.append(f"  {date}: {prog.progression_type[:100]}")
        lines.append("")

        # Recurrences
        lines.append("RECURRENCES:")
        for idx, rec in enumerate(extractions.recurrences):
            date = rec.date_mentioned or "unknown date"
            lines.append(f"  {date}: {rec.recurrence_type[:100]}")
        lines.append("")

        # Metastases
        lines.append("METASTASES:")
        for idx, met in enumerate(extractions.metastases):
            date = met.date_mentioned or "unknown date"
            lines.append(f"  {date}: {met.location}")
        lines.append("")

        return "\n".join(lines)
