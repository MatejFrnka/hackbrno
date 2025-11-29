import os
import asyncio
import hashlib
import pandas as pd
import typing
from openai import AsyncOpenAI

from llm_extraction.models import Question, MedicalRecord, PatientData
from llm_extraction.extraction import FeatureExtractor, HighlightExtractor, HighlightFilter, PatientSummaryExtractor, BatchSummaryExtractor
from llm_extraction.span_matcher import SpanMatcher


class LLMBackend:
    def process_patient(self, patient: pd.DataFrame, questions: typing.List[typing.Tuple[int, str, str]]):
        # TODO
        return {'input': [patient, questions]}

    def summarize_patient(self, patient: pd.DataFrame) -> str:
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

    def __init__(self):
        """
        Initialize the backend with OpenAI client and extraction components.

        Configuration is loaded from environment variables:
        - OPENAI_API_KEY: API key for authentication (required)
        - OPENAI_URL: Base URL for API (default: https://api.openai.com/v1)
        - OPENAI_MODEL: Model to use for extraction (default: gpt-5.1)
        """
        # Initialize AsyncOpenAI client from environment
        self.client = AsyncOpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_URL", "https://api.openai.com/v1")
        )
        self.model = os.getenv("OPENAI_MODEL", "gpt-5.1")

        # Initialize extraction components
        self.extractor = FeatureExtractor(self.client, model=self.model)
        self.span_matcher = SpanMatcher(similarity_threshold=0.9)

        # Initialize highlight components
        self.highlight_extractor = HighlightExtractor(self.client, model=self.model)
        self.highlight_filter = HighlightFilter(self.client, model=self.model)

        # Initialize patient summary extractor
        self.patient_summary_extractor = PatientSummaryExtractor(self.client, model=self.model)

        # Initialize batch summary extractor
        self.batch_summary_extractor = BatchSummaryExtractor(self.client, model=self.model)

    def prepare_patient_data(self, patient: pd.DataFrame) -> PatientData:
        """
        Prepare PatientData object from a DataFrame.

        Args:
            patient: DataFrame with columns [patient_id, record_id, date, type, text]

        Returns:
            PatientData object with MedicalRecord objects
        """
        patient_id = str(patient.iloc[0]['patient_id'])

        records = [
            MedicalRecord(
                record_id=row['record_id'],
                patient_id=patient_id,
                date=str(row['date']),
                record_type=str(row['type']),
                text=str(row['text']),
                text_hash=hashlib.sha256(str(row['text']).encode('utf-8')).hexdigest()
            )
            for _, row in patient.iterrows()
        ]

        return PatientData(patient_id=patient_id, records=records)

    def prepare_questions(self, questions: typing.List[typing.Tuple[int, str, str]]) -> typing.List[Question]:
        """
        Convert list of question tuples to Question objects.

        Args:
            questions: List of (question_id, question_text, additional_instructions) tuples

        Returns:
            List of Question objects
        """
        return [
            Question(
                question_id=qid,
                text=text,
                additional_instructions=instructions
            )
            for qid, text, instructions in questions
        ]

    def process_patient(self, patient: pd.DataFrame, questions: typing.List[typing.Tuple[int, str, str]]):
        """
        Extract medical information from patient records (synchronous wrapper).

        Args:
            patient: DataFrame with columns [patient_id, record_id, date, type, text]
            questions: List of (question_id, question_text, additional_instructions) tuples

        Returns:
            Dictionary with patient_id, total_citations, and list of citations with spans
        """
        # Prepare patient data
        patient_data = self.prepare_patient_data(patient)
        questions_objects = self.prepare_questions(questions)

        # Extract and process citations
        sorted_citations = asyncio.run(self._extract_citations(patient_data, questions_objects))

        # Extract and process highlights
        sorted_highlights = asyncio.run(self._extract_highlights(patient_data))

        # Generate patient summary
        summary = asyncio.run(self._summarize_patient(patient_data))

        # Format results as dictionary
        return {
            "patient_id": patient_data.patient_id,
            "total_citations": len(sorted_citations),
            "summary_long": summary,
            "citations": [
                {
                    "question_id": c.question_id,
                    "quoted_text": c.quoted_text,
                    "confidence": c.confidence,
                    "record_id": c.record_id,
                    "start_char": c.start_char,
                    "end_char": c.end_char
                }
                for c in sorted_citations
            ],
            "highlights": [
                {
                    "quoted_text": h.quoted_text,
                    "note": h.note,
                    "record_id": h.record_id,
                    "start_char": h.start_char,
                    "end_char": h.end_char
                }
                for h in sorted_highlights
            ]
        }

    async def _process_patient_async(self, patient: pd.DataFrame, questions: typing.List[typing.Tuple[int, str, str]]):
        """
        Extract medical information from patient records asynchronously.

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

        # Extract and process citations
        sorted_citations = await self._extract_citations(patient_data, question_objects)

        # Extract and process highlights
        sorted_highlights = await self._extract_highlights(patient_data)

        # Generate patient summary
        summary = await self._summarize_patient_async(patient)

        # Format results as dictionary
        return {
            "patient_id": patient_id,
            "total_citations": len(sorted_citations),
            "summary_long": summary,
            "citations": [
                {
                    "question_id": c.question_id,
                    "quoted_text": c.quoted_text,
                    "confidence": c.confidence,
                    "record_id": c.record_id,
                    "start_char": c.start_char,
                    "end_char": c.end_char
                }
                for c in sorted_citations
            ],
            "highlights": [
                {
                    "quoted_text": h.quoted_text,
                    "note": h.note,
                    "record_id": h.record_id,
                    "start_char": h.start_char,
                    "end_char": h.end_char
                }
                for h in sorted_highlights
            ]
        }

    async def _extract_citations(self, patient_data: PatientData, question_objects: typing.List[Question]):
        """
        Extract citations from patient data and match to exact character positions.

        Args:
            patient_data: Patient data with medical records
            question_objects: List of questions to answer with citations

        Returns:
            List of citations sorted by record_id and start_char
        """
        # Extract citations using LLM (async)
        extraction_results = await self.extractor.extract_patient_features(
            patient_data,
            question_objects
        )

        # Match citations to exact character positions
        citations_with_spans = self.span_matcher.match_all_citations(
            extraction_results,
            patient_data
        )

        # Sort citations by record_id (ascending), then start_char (ascending)
        return sorted(
            citations_with_spans,
            key=lambda c: (c.record_id, c.start_char)
        )

    async def _extract_highlights(self, patient_data: PatientData):
        """
        Extract and filter highlights from patient data (two-stage process).

        Stage 1: Extract highlights per-record
        Stage 2: Filter to most important highlights

        Args:
            patient_data: Patient data with medical records

        Returns:
            List of filtered highlights sorted by record_id and start_char
        """
        # Stage 1: Extract highlights per-record
        highlight_results = await self.highlight_extractor.extract_highlights(patient_data)

        # Stage 1b: Add span information to highlights
        highlights_with_spans = self.span_matcher.match_highlight_citations(
            highlight_results,
            patient_data
        )

        # Stage 2: Filter to most important highlights
        filtered_highlights = await self.highlight_filter.filter_highlights(
            highlights_with_spans,
            patient_data
        )

        # Sort filtered highlights by record_id, then start_char
        return sorted(
            filtered_highlights,
            key=lambda h: (h.record_id, h.start_char)
        )

    async def _summarize_patient(self, patient_data: PatientData) -> str:
        """
        Generate patient summary asynchronously.

        Args:
            patient_data: Patient data with medical records

        Returns:
            String containing narrative summary of patient journey
        """
        # Generate summary using LLM (async)
        return await self.patient_summary_extractor.summarize_patient_async(patient_data)

    def summarize_patient(self, patient: pd.DataFrame) -> str:
        """
        Generate a comprehensive narrative summary of patient's medical journey.

        Args:
            patient: DataFrame with columns [patient_id, record_id, date, type, text]

        Returns:
            String containing narrative summary of patient journey
        """
        # Prepare patient data
        patient_data = self.prepare_patient_data(patient)

        # Generate patient summary
        return asyncio.run(self._summarize_patient(patient_data))

    async def _summarize_batch(self, patient_summaries: typing.List[typing.Tuple[str, str]]) -> str:
        """
        Generate batch summary asynchronously.

        Args:
            patient_summaries: List of (patient_id, summary) tuples

        Returns:
            String containing comprehensive summary of entire patient cohort
        """
        # Generate batch summary using LLM (async)
        return await self.batch_summary_extractor.summarize_batch_async(patient_summaries)

    def summarize_batch(self, patient_summaries: typing.List[typing.Tuple[str, str]]) -> str:
        """
        Generate a comprehensive summary across multiple patients for cohort-level overview.

        Args:
            patient_summaries: List of (patient_id, summary) tuples where each tuple contains:
                - patient_id (str): Patient identifier (e.g., "HACK01")
                - summary (str): Individual patient summary generated by summarize_patient()

        Returns:
            String containing narrative summary of entire patient cohort

        Example:
            >>> patient_summaries = [
            ...     ("HACK01", "Pacientka s karcinomem prsu..."),
            ...     ("HACK02", "Pacientka s metastázami..."),
            ... ]
            >>> batch_summary = backend.summarize_batch(patient_summaries)
        """
        # Generate batch summary
        return asyncio.run(self._summarize_batch(patient_summaries))
