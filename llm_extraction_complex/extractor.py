"""
LLM-based feature extractor for Czech medical records.

Supports two extraction modes:
- Bulk: Process all records in one API call (faster, better cross-record context)
- Per-Record: Process each record individually (safer for long histories)
"""

from typing import List, Literal
from openai import OpenAI
from .models import PatientData, SingleRecordExtractionResult
from .prompts import EXTRACTION_SYSTEM_PROMPT_SINGLE, EXTRACTION_SYSTEM_PROMPT_BULK
from .utils import estimate_tokens


class FeatureExtractor:
    """Extract medical features from patient records using LLM"""

    def __init__(self, client: OpenAI, model: str = "gpt-4o-2024-08-06"):
        """
        Initialize feature extractor.

        Args:
            client: OpenAI client instance
            model: Model to use for extraction
        """
        self.client = client
        self.model = model

    def extract_features(self,
                        patient_data: PatientData,
                        mode: Literal["auto", "bulk", "per_record"] = "auto") -> List[SingleRecordExtractionResult]:
        """
        Extract features from patient records.

        Args:
            patient_data: Patient data to extract from
            mode: Extraction mode ("auto", "bulk", or "per_record")

        Returns:
            List of extraction results (one per record)
        """
        # Automatic mode selection
        if mode == "auto":
            total_tokens = estimate_tokens(patient_data)
            num_records = len(patient_data.records)

            if num_records <= 15 and total_tokens < 8000:
                mode = "bulk"
                print(f"Auto mode: Using BULK extraction ({num_records} records, ~{total_tokens} tokens)")
            else:
                mode = "per_record"
                print(f"Auto mode: Using PER-RECORD extraction ({num_records} records, ~{total_tokens} tokens)")

        # Execute appropriate mode
        if mode == "bulk":
            return self._extract_bulk(patient_data)
        else:
            return self._extract_per_record(patient_data)

    def _extract_per_record(self, patient_data: PatientData) -> List[SingleRecordExtractionResult]:
        """
        Extract features from each record individually.

        Args:
            patient_data: Patient data

        Returns:
            List of extraction results
        """
        results = []

        print(f"Extracting features from {len(patient_data.records)} records (per-record mode)...")

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
                        {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT_SINGLE},
                        {"role": "user", "content": user_message}
                    ],
                    response_format=SingleRecordExtractionResult
                )

                result = response.choices[0].message.parsed

                # Ensure record_id is set correctly
                result.record_id = record.record_id

                results.append(result)

                # Log extraction summary
                total_extractions = (
                    len(result.diagnosis_dates) +
                    len(result.tnm_classifications) +
                    len(result.hormone_receptors) +
                    len(result.external_treatments) +
                    len(result.progressions) +
                    len(result.recurrences) +
                    len(result.metastases)
                )
                print(f"    → Extracted {total_extractions} features")

            except Exception as e:
                print(f"    ERROR: Failed to extract from {record.record_id}: {e}")
                # Return empty result for this record
                results.append(SingleRecordExtractionResult(record_id=record.record_id))

        return results

    def _extract_bulk(self, patient_data: PatientData) -> List[SingleRecordExtractionResult]:
        """
        Extract features from all records in one API call.

        Args:
            patient_data: Patient data

        Returns:
            List of extraction results
        """
        print(f"Extracting features from {len(patient_data.records)} records (bulk mode)...")

        # Format all records with clear delimiters
        records_text = "\n\n".join([
            f"=== ZÁZNAM {r.record_id} | Datum: {r.date} | Typ: {r.record_type} ===\n{r.text}"
            for r in patient_data.records
        ])

        try:
            # Call OpenAI with structured output
            # Note: We need to wrap multiple results in a container
            class BulkExtractionResult(BaseModel):
                """Container for bulk extraction results"""
                results: List[SingleRecordExtractionResult]

            response = self.client.beta.chat.completions.parse(
                model=self.model,
                messages=[
                    {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT_BULK},
                    {"role": "user", "content": records_text}
                ],
                response_format=BulkExtractionResult
            )

            bulk_result = response.choices[0].message.parsed
            results = bulk_result.results

            # Verify all records were processed
            result_ids = {r.record_id for r in results}
            expected_ids = {r.record_id for r in patient_data.records}

            if result_ids != expected_ids:
                missing = expected_ids - result_ids
                extra = result_ids - expected_ids
                print(f"  Warning: Record ID mismatch!")
                if missing:
                    print(f"    Missing: {missing}")
                    # Add empty results for missing records
                    for record_id in missing:
                        results.append(SingleRecordExtractionResult(record_id=record_id))
                if extra:
                    print(f"    Extra: {extra}")

            print(f"  → Extracted features from {len(results)} records")

            return results

        except Exception as e:
            print(f"  ERROR: Bulk extraction failed: {e}")
            print(f"  Falling back to per-record extraction...")
            return self._extract_per_record(patient_data)


# Add the missing import
from pydantic import BaseModel
