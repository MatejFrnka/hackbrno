"""
Feature extraction using OpenAI with dynamic questions.
"""

import asyncio
from typing import List
from openai import AsyncOpenAI
from pydantic import BaseModel

from llm_extraction.models import PatientData, Question, ExtractionCitation
from llm_extraction.prompts import generate_extraction_prompt


class ExtractionResult(BaseModel):
    """LLM response structure"""
    citations: List[ExtractionCitation]


class FeatureExtractor:
    """Extract citations from medical records using LLM with dynamic questions"""

    def __init__(self, client: AsyncOpenAI, model: str = "gpt-4o"):
        """
        Args:
            client: AsyncOpenAI client instance
            model: OpenAI model to use for extraction
        """
        self.client = client
        self.model = model

    async def _extract_single_record(
        self,
        record,
        system_prompt: str,
        idx: int,
        total: int
    ) -> dict:
        """
        Extract features from a single record asynchronously with retry logic.

        Args:
            record: Medical record to process
            system_prompt: System prompt with questions
            idx: Record index (for logging)
            total: Total number of records (for logging)

        Returns:
            Dict with record_id and citations
        """
        print(f"  Processing record {idx + 1}/{total}: {record.record_id} ({record.date})")

        # Format record for LLM
        user_message = f"""Record ID: {record.record_id}
Datum: {record.date}
Typ: {record.record_type}

{record.text}
"""

        max_retries = 3
        base_delay = 1.0  # Start with 1 second

        for attempt in range(max_retries):
            try:
                # Call OpenAI with structured output
                response = await self.client.beta.chat.completions.parse(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message}
                    ],
                    response_format=ExtractionResult,
                    temperature=0
                )

                result = response.choices[0].message.parsed

                print(f"    → Extracted {len(result.citations)} citations")

                return {
                    'record_id': record.record_id,
                    'citations': result.citations
                }

            except Exception as e:
                if attempt < max_retries - 1:
                    # Calculate exponential backoff delay: 1s, 2s, 4s
                    delay = base_delay * (2 ** attempt)
                    print(f"    WARNING: Attempt {attempt + 1}/{max_retries} failed for {record.record_id}: {e}")
                    print(f"    Retrying in {delay}s...")
                    await asyncio.sleep(delay)
                else:
                    # Final attempt failed
                    print(f"    ERROR: All {max_retries} attempts failed for {record.record_id}: {e}")
                    return {
                        'record_id': record.record_id,
                        'citations': []
                    }

    async def extract_patient_features(
        self,
        patient_data: PatientData,
        questions: List[Question]
    ) -> List[dict]:
        """
        Extract features from all patient records asynchronously.

        Args:
            patient_data: Parsed patient data with medical records
            questions: List of questions to answer

        Returns:
            List of dicts: {'record_id': str, 'citations': List[ExtractionCitation]}
        """
        # Generate system prompt with questions
        system_prompt = generate_extraction_prompt(questions)

        print(f"Extracting features from {len(patient_data.records)} records...")

        # Create async tasks for all records
        tasks = [
            self._extract_single_record(record, system_prompt, idx, len(patient_data.records))
            for idx, record in enumerate(patient_data.records)
        ]

        # Use as_completed to process results as they arrive
        results = []
        for coro in asyncio.as_completed(tasks):
            result = await coro
            results.append(result)

        return results
