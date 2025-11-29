"""
Feature extraction using OpenAI with dynamic questions.
"""

from typing import List
from openai import OpenAI
from pydantic import BaseModel

from llm_extraction.models import PatientData, Question, ExtractionCitation
from llm_extraction.prompts import generate_extraction_prompt


class ExtractionResult(BaseModel):
    """LLM response structure"""
    citations: List[ExtractionCitation]


class FeatureExtractor:
    """Extract citations from medical records using LLM with dynamic questions"""

    def __init__(self, client: OpenAI, model: str = "gpt-4o"):
        """
        Args:
            client: OpenAI client instance
            model: OpenAI model to use for extraction
        """
        self.client = client
        self.model = model

    def extract_patient_features(
        self,
        patient_data: PatientData,
        questions: List[Question]
    ) -> List[dict]:
        """
        Extract features from all patient records.

        Args:
            patient_data: Parsed patient data with medical records
            questions: List of questions to answer

        Returns:
            List of dicts: {'record_id': str, 'citations': List[ExtractionCitation]}
        """
        results = []

        # Generate system prompt with questions
        system_prompt = generate_extraction_prompt(questions)

        print(f"Extracting features from {len(patient_data.records)} records...")

        for idx, record in enumerate(patient_data.records):
            print(f"  Processing record {idx + 1}/{len(patient_data.records)}: {record.record_id} ({record.date})")

            # Format record for LLM
            user_message = f"""Record ID: {record.record_id}
Datum: {record.date}
Typ: {record.record_type}

{record.text}
"""

            try:
                # Call OpenAI with structured output
                response = self.client.beta.chat.completions.parse(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message}
                    ],
                    response_format=ExtractionResult,
                    temperature=0
                )

                result = response.choices[0].message.parsed

                results.append({
                    'record_id': record.record_id,
                    'citations': result.citations
                })

                print(f"    → Extracted {len(result.citations)} citations")

            except Exception as e:
                print(f"    ERROR: Failed to extract from {record.record_id}: {e}")
                results.append({
                    'record_id': record.record_id,
                    'citations': []
                })

        return results
