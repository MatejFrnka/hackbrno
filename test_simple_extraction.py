"""
Test script for simplified extraction pipeline.

Tests the simplified workflow using records.csv:
- Load patient data from CSV by patient_id
- Dynamic question loading from mock_data.py
- LLM citation extraction
- Span matching with normalization + Levenshtein
"""

import os
import json
import hashlib
import pandas as pd
from openai import OpenAI
from dotenv import load_dotenv

from data.mock_data import mock_questions
from llm_extraction.models import Question, MedicalRecord, PatientData
from llm_extraction.extraction import FeatureExtractor
from llm_extraction.span_matcher import SpanMatcher


def load_patient_from_csv(patient_id: str, csv_path: str = "data/records.csv") -> PatientData:
    """
    Load patient data from records.csv.

    Args:
        patient_id: Patient ID (e.g., "HACK01")
        csv_path: Path to CSV file

    Returns:
        PatientData object
    """
    print(f"Loading patient {patient_id} from {csv_path}...")

    # Load CSV
    df = pd.read_csv(csv_path)

    # Filter for patient
    patient_df = df[df['patient_id'] == patient_id].copy()

    if len(patient_df) == 0:
        raise ValueError(f"No records found for patient_id: {patient_id}")

    # Sort by date
    patient_df = patient_df.sort_values('date')

    # Build records
    records = []
    seen_hashes = set()
    duplicate_count = 0

    for idx, row in patient_df.iterrows():
        text = str(row['text'])
        text_hash = hashlib.sha256(text.encode('utf-8')).hexdigest()

        # Skip duplicates
        if text_hash in seen_hashes:
            duplicate_count += 1
            continue

        seen_hashes.add(text_hash)

        record = MedicalRecord(
            record_id=f"{patient_id}_{len(records)}",
            patient_id=patient_id,
            date=str(row['date']),
            record_type=str(row['type']),
            text=text,
            text_hash=text_hash
        )
        records.append(record)

    print(f"  → {len(records)} unique records ({duplicate_count} duplicates removed)")

    return PatientData(patient_id=patient_id, records=records)


def main():
    # Load environment variables
    load_dotenv()

    print("=" * 80)
    print("Simplified Medical Information Extraction Pipeline - Test Run")
    print("=" * 80)
    print()

    # Initialize components
    print("Initializing components...")
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    extractor = FeatureExtractor(client, model="gpt-4o")
    span_matcher = SpanMatcher(similarity_threshold=0.9)
    print("✓ Components initialized")
    print()

    # Convert mock questions to Question objects
    questions = [
        Question(question_id=qid, text=text, additional_instructions=instructions)
        for qid, text, instructions in mock_questions
    ]
    print(f"Loaded {len(questions)} questions from mock_data.py")
    print()

    # Load patient data from CSV
    patient_id = "HACK01"
    patient_data = load_patient_from_csv(patient_id)
    print()

    # Extract citations
    extraction_results = extractor.extract_patient_features(patient_data, questions)
    print()

    # Match spans
    citations_with_spans = span_matcher.match_all_citations(extraction_results, patient_data)
    print()

    # Print summary
    print("=" * 80)
    print("Extraction Summary")
    print("=" * 80)
    print(f"Total citations with spans: {len(citations_with_spans)}")
    print()

    # Group by question
    by_question = {}
    for citation in citations_with_spans:
        qid = citation.question_id
        if qid not in by_question:
            by_question[qid] = []
        by_question[qid].append(citation)

    print("Citations by question:")
    for qid in sorted(by_question.keys()):
        question_text = next((q.text for q in questions if q.question_id == qid), "Unknown")
        print(f"  Q{qid} ({question_text}): {len(by_question[qid])} citations")
    print()

    # Show first 10 citations
    print("Sample citations (first 10):")
    for i, citation in enumerate(citations_with_spans[:10]):
        question_text = next((q.text for q in questions if q.question_id == citation.question_id), "Unknown")
        print(f"  [{i+1}] Q{citation.question_id} ({question_text})")
        print(f"      Text: '{citation.quoted_text[:60]}...'")
        print(f"      Record: {citation.record_id}")
        print(f"      Span: chars {citation.start_char}-{citation.end_char}")
        print(f"      Confidence: {citation.confidence}")
        print()

    # Save results to JSON
    output_path = "output/HACK01_simple_extractions.json"
    os.makedirs("output", exist_ok=True)

    output_data = {
        "patient_id": patient_data.patient_id,
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

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    print(f"Results saved to: {output_path}")
    print()

    print("=" * 80)
    print("Test completed successfully!")
    print("=" * 80)


if __name__ == "__main__":
    main()
