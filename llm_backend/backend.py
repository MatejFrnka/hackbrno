import os
import hashlib
import pandas as pd
import typing
from openai import OpenAI

from llm_extraction.models import Question, MedicalRecord, PatientData
from llm_extraction.extraction import FeatureExtractor
from llm_extraction.span_matcher import SpanMatcher


class LLMBackend:
    def process_patient(self, patient: pd.DataFrame, questions: typing.List[typing.Tuple[int, str, str]]):
        # TODO
        return {'input': [patient, questions]}

    def summarize_patient(self, patient: pd.DataFrame, processed_data) -> str:
        # TODO
        return 'Patient is ...'

    # Each patient is a tuple of the original data, processed data (from process_patient())
    # and patient summary (from summarize_patient())
    def summarize_batch(self, patients: typing.List[typing.Tuple[pd.DataFrame, typing.Any, str]]) -> str:
        # TODO
        return 'You have 10 patients ...'


class LLMBackendBase(LLMBackend):
    """
    Base implementation of LLMBackend with medical information extraction.

    Uses FeatureExtractor and SpanMatcher to extract citations from patient records
    and map them to exact character positions.
    """

    def __init__(self, model: str = "gpt-4o"):
        """
        Initialize the backend with OpenAI client and extraction components.

        Args:
            model: OpenAI model to use for extraction (default: gpt-4o)
        """
        # Initialize OpenAI client from environment
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = model

        # Initialize extraction components
        self.extractor = FeatureExtractor(self.client, model=self.model)
        self.span_matcher = SpanMatcher(similarity_threshold=0.9)

    def process_patient(self, patient: pd.DataFrame, questions: typing.List[typing.Tuple[int, str, str]]):
        """
        Extract medical information from patient records.

        Args:
            patient: DataFrame with columns [patient_id, record_id, date, type, text]
            questions: List of (question_id, question_text, additional_instructions) tuples

        Returns:
            Dictionary with patient_id, total_citations, and list of citations with spans
        """
        # Validate inputs
        if patient.empty:
            raise ValueError("Patient DataFrame is empty")
        if not questions:
            raise ValueError("Questions list is empty")

        # Get patient_id from first row
        patient_id = str(patient.iloc[0]['patient_id'])

        # Convert DataFrame to MedicalRecord objects
        records = []
        seen_hashes = set()

        for idx, row in patient.iterrows():
            text = str(row['text'])
            text_hash = hashlib.sha256(text.encode('utf-8')).hexdigest()

            # Skip duplicates - For now, do not use duplicate removal
            # if text_hash in seen_hashes:
            #     continue

            # seen_hashes.add(text_hash)

            record = MedicalRecord(
                record_id=row['record_id'],
                patient_id=patient_id,
                date=str(row['date']),
                record_type=str(row['type']),
                text=text,
                text_hash=text_hash
            )
            records.append(record)

        # Create PatientData object
        patient_data = PatientData(patient_id=patient_id, records=records)

        # Convert question tuples to Question objects
        question_objects = [
            Question(
                question_id=qid,
                text=text,
                additional_instructions=instructions
            )
            for qid, text, instructions in questions
        ]

        # Extract citations using LLM
        extraction_results = self.extractor.extract_patient_features(
            patient_data,
            question_objects
        )

        # Match citations to exact character positions
        citations_with_spans = self.span_matcher.match_all_citations(
            extraction_results,
            patient_data
        )

        # Format results as dictionary
        return {
            "patient_id": patient_id,
            "total_citations": len(citations_with_spans),
            "citations": [
                {
                    "question_id": c.question_id,
                    "quoted_text": c.quoted_text,
                    "confidence": c.confidence,
                    "record_id": c.record_id,
                    "start_char": c.start_char,
                    "end_char": c.end_char
                }
                for c in citations_with_spans
            ]
        }

    def summarize_patient(self, patient: pd.DataFrame, processed_data) -> str:
        """Not currently used."""
        raise NotImplementedError("summarize_patient is not currently used")

    def summarize_batch(self, patients: typing.List[typing.Tuple[pd.DataFrame, typing.Any, str]]) -> str:
        """Not currently used."""
        raise NotImplementedError("summarize_batch is not currently used")
