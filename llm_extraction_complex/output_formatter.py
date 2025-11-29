"""
Output formatting for final JSON results.

Creates comprehensive JSON output with all extractions, timelines, and metadata.
"""

from typing import Dict, Any
from datetime import datetime
from .models import (
    PatientData,
    PatientExtractionResult,
    DeduplicationResult,
    InconsistencyDetection,
    PatientTimeline
)


class OutputFormatter:
    """Format final JSON output"""

    def format_output(self,
                     patient_data: PatientData,
                     extractions: PatientExtractionResult,
                     deduplication: DeduplicationResult,
                     inconsistencies: list[InconsistencyDetection],
                     timeline: PatientTimeline) -> Dict[str, Any]:
        """
        Create comprehensive JSON output.

        Args:
            patient_data: Original patient data
            extractions: All extractions with spans
            deduplication: Deduplication results
            inconsistencies: Detected inconsistencies
            timeline: Patient timeline

        Returns:
            Dictionary ready for JSON serialization
        """
        return {
            "metadata": self._format_metadata(patient_data),
            "extractions": self._format_extractions(extractions),
            "deduplication": self._format_deduplication(deduplication),
            "inconsistencies": self._format_inconsistencies(inconsistencies),
            "timeline": self._format_timeline(timeline)
        }

    def _format_metadata(self, patient_data: PatientData) -> Dict[str, Any]:
        """Format patient metadata"""
        return {
            "patient_id": patient_data.patient_id,
            "num_records": len(patient_data.records),
            "duplicates_removed": patient_data.duplicate_count,
            "date_range": {
                "first": patient_data.records[0].date if patient_data.records else None,
                "last": patient_data.records[-1].date if patient_data.records else None
            },
            "record_types": self._count_record_types(patient_data),
            "processing_timestamp": datetime.now().isoformat()
        }

    def _count_record_types(self, patient_data: PatientData) -> Dict[str, int]:
        """Count records by type"""
        counts = {}
        for record in patient_data.records:
            counts[record.record_type] = counts.get(record.record_type, 0) + 1
        return counts

    def _format_extractions(self, extractions: PatientExtractionResult) -> Dict[str, Any]:
        """Format all extractions"""
        return {
            "diagnosis_dates": [self._format_diagnosis_date(dx) for dx in extractions.diagnosis_dates],
            "tnm_classifications": [self._format_tnm(tnm) for tnm in extractions.tnm_classifications],
            "hormone_receptors": [self._format_receptor(rec) for rec in extractions.hormone_receptors],
            "external_treatments": [self._format_treatment(tx) for tx in extractions.external_treatments],
            "progressions": [self._format_progression(prog) for prog in extractions.progressions],
            "recurrences": [self._format_recurrence(rec) for rec in extractions.recurrences],
            "metastases": [self._format_metastases(met) for met in extractions.metastases],
            "counts": {
                "diagnosis_dates": len(extractions.diagnosis_dates),
                "tnm_classifications": len(extractions.tnm_classifications),
                "hormone_receptors": len(extractions.hormone_receptors),
                "external_treatments": len(extractions.external_treatments),
                "progressions": len(extractions.progressions),
                "recurrences": len(extractions.recurrences),
                "metastases": len(extractions.metastases)
            }
        }

    def _format_diagnosis_date(self, dx) -> Dict[str, Any]:
        """Format diagnosis date extraction"""
        return {
            "date": dx.date_value,
            "inferred": dx.inferred,
            "notes": dx.notes,
            "spans": [self._format_span(span) for span in dx.spans]
        }

    def _format_tnm(self, tnm) -> Dict[str, Any]:
        """Format TNM classification"""
        return {
            "value": tnm.tnm_value,
            "type": tnm.classification_type,
            "spans": [self._format_span(span) for span in tnm.spans]
        }

    def _format_receptor(self, receptor) -> Dict[str, Any]:
        """Format hormone receptor"""
        return {
            "type": receptor.receptor_type,
            "value": receptor.value,
            "spans": [self._format_span(span) for span in receptor.spans]
        }

    def _format_treatment(self, treatment) -> Dict[str, Any]:
        """Format external treatment"""
        return {
            "description": treatment.treatment_description,
            "location": treatment.location,
            "spans": [self._format_span(span) for span in treatment.spans]
        }

    def _format_progression(self, prog) -> Dict[str, Any]:
        """Format progression"""
        return {
            "type": prog.progression_type,
            "date": prog.date_mentioned,
            "spans": [self._format_span(span) for span in prog.spans]
        }

    def _format_recurrence(self, rec) -> Dict[str, Any]:
        """Format recurrence"""
        return {
            "type": rec.recurrence_type,
            "date": rec.date_mentioned,
            "spans": [self._format_span(span) for span in rec.spans]
        }

    def _format_metastases(self, met) -> Dict[str, Any]:
        """Format metastases"""
        return {
            "location": met.location,
            "date": met.date_mentioned,
            "spans": [self._format_span(span) for span in met.spans]
        }

    def _format_span(self, span) -> Dict[str, Any]:
        """Format text span"""
        return {
            "text": span.text,
            "start": span.start_char,
            "end": span.end_char,
            "record_id": span.record_id,
            "confidence": span.confidence,
            "match_index": span.match_index
        }

    def _format_deduplication(self, dedup: DeduplicationResult) -> Dict[str, Any]:
        """Format deduplication results"""
        return {
            "diagnosis_date_duplicates": [self._format_duplicate_group(g) for g in dedup.diagnosis_date_duplicates],
            "tnm_duplicates": [self._format_duplicate_group(g) for g in dedup.tnm_duplicates],
            "receptor_duplicates": [self._format_duplicate_group(g) for g in dedup.receptor_duplicates],
            "external_treatment_duplicates": [self._format_duplicate_group(g) for g in dedup.external_treatment_duplicates],
            "progression_duplicates": [self._format_duplicate_group(g) for g in dedup.progression_duplicates],
            "recurrence_duplicates": [self._format_duplicate_group(g) for g in dedup.recurrence_duplicates],
            "metastases_duplicates": [self._format_duplicate_group(g) for g in dedup.metastases_duplicates],
            "summary": {
                "total_groups": (
                    len(dedup.diagnosis_date_duplicates) +
                    len(dedup.tnm_duplicates) +
                    len(dedup.receptor_duplicates) +
                    len(dedup.external_treatment_duplicates) +
                    len(dedup.progression_duplicates) +
                    len(dedup.recurrence_duplicates) +
                    len(dedup.metastases_duplicates)
                )
            }
        }

    def _format_duplicate_group(self, group) -> Dict[str, Any]:
        """Format duplicate group"""
        return {
            "canonical_extraction": group.canonical_extraction,
            "duplicate_indices": group.duplicate_indices,
            "reasoning": group.reasoning
        }

    def _format_inconsistencies(self, inconsistencies: list) -> Dict[str, Any]:
        """Format inconsistencies"""
        return {
            "items": [self._format_inconsistency(inc) for inc in inconsistencies],
            "summary": {
                "total": len(inconsistencies),
                "by_severity": {
                    "critical": sum(1 for inc in inconsistencies if inc.severity == "critical"),
                    "moderate": sum(1 for inc in inconsistencies if inc.severity == "moderate"),
                    "minor": sum(1 for inc in inconsistencies if inc.severity == "minor")
                },
                "by_type": self._count_inconsistency_types(inconsistencies)
            }
        }

    def _format_inconsistency(self, inc) -> Dict[str, Any]:
        """Format single inconsistency"""
        return {
            "type": inc.inconsistency_type,
            "severity": inc.severity,
            "description": inc.description,
            "related_feature": inc.related_feature,
            "involved_records": inc.involved_records
        }

    def _count_inconsistency_types(self, inconsistencies: list) -> Dict[str, int]:
        """Count inconsistencies by type"""
        counts = {}
        for inc in inconsistencies:
            counts[inc.inconsistency_type] = counts.get(inc.inconsistency_type, 0) + 1
        return counts

    def _format_timeline(self, timeline: PatientTimeline) -> Dict[str, Any]:
        """Format timeline"""
        return {
            "diagnosis": self._format_feature_timeline(timeline.diagnosis_timeline),
            "tnm": self._format_feature_timeline(timeline.tnm_timeline),
            "receptors": self._format_feature_timeline(timeline.receptor_timeline),
            "treatment": self._format_feature_timeline(timeline.treatment_timeline),
            "progression": self._format_feature_timeline(timeline.progression_timeline),
            "recurrence": self._format_feature_timeline(timeline.recurrence_timeline),
            "metastases": self._format_feature_timeline(timeline.metastases_timeline),
            "overall_narrative": timeline.overall_narrative
        }

    def _format_feature_timeline(self, feature_timeline) -> Dict[str, Any]:
        """Format feature timeline"""
        return {
            "feature_name": feature_timeline.feature_name,
            "events": [self._format_timeline_event(event) for event in feature_timeline.events],
            "narrative": feature_timeline.narrative
        }

    def _format_timeline_event(self, event) -> Dict[str, Any]:
        """Format timeline event"""
        return {
            "date": event.date,
            "description": event.description,
            "significance": event.significance
        }
