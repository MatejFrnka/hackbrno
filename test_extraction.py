"""
Test script for medical information extraction.

Tests the extraction pipeline on HACK01.xml.
"""

import os
import json
from openai import OpenAI
from llm_extraction_complex.xml_parser import XMLParser
from llm_extraction_complex.extractor import FeatureExtractor
from llm_extraction_complex.span_calculator import SpanCalculator
from dotenv import load_dotenv


def main():
    # Load environment variables
    load_dotenv()

    # Load API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not found in environment")

    print("=" * 80)
    print("Medical Information Extraction - Test Run")
    print("=" * 80)
    print()

    # Initialize components
    print("Initializing components...")
    client = OpenAI(api_key=api_key)
    xml_parser = XMLParser()
    extractor = FeatureExtractor(client, model="gpt-4o-2024-08-06")
    span_calculator = SpanCalculator()
    print("✓ Components initialized")
    print()

    # Step 1: Parse XML
    print("Step 1: Parsing XML file...")
    patient_data = xml_parser.parse_patient_file("data/HACK01.xml")
    print(f"✓ Parsed {patient_data.patient_id}")
    print(f"  - {len(patient_data.records)} records")
    print(f"  - {patient_data.duplicate_count} duplicates removed")
    print()

    # Step 2: Extract features
    print("Step 2: Extracting features with LLM...")
    extractions = extractor.extract_features(patient_data, mode="per_record")
    print(f"✓ Extracted features from {len(extractions)} records")

    # Count total extractions
    total_count = 0
    for result in extractions:
        total_count += (
            len(result.diagnosis_dates) +
            len(result.tnm_classifications) +
            len(result.hormone_receptors) +
            len(result.external_treatments) +
            len(result.progressions) +
            len(result.recurrences) +
            len(result.metastases)
        )
    print(f"  - Total: {total_count} feature extractions")
    print()

    # Step 3: Calculate spans
    print("Step 3: Calculating character spans...")
    extractions_with_spans = span_calculator.calculate_all_spans(extractions, patient_data)
    print(f"✓ Calculated spans for all extractions")
    print(f"  - Diagnosis dates: {len(extractions_with_spans.diagnosis_dates)}")
    print(f"  - TNM classifications: {len(extractions_with_spans.tnm_classifications)}")
    print(f"  - Hormone receptors: {len(extractions_with_spans.hormone_receptors)}")
    print(f"  - External treatments: {len(extractions_with_spans.external_treatments)}")
    print(f"  - Progressions: {len(extractions_with_spans.progressions)}")
    print(f"  - Recurrences: {len(extractions_with_spans.recurrences)}")
    print(f"  - Metastases: {len(extractions_with_spans.metastases)}")
    print()

    # Step 4: Save results
    print("Step 4: Saving results...")
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)

    output_file = f"{output_dir}/{patient_data.patient_id}_extractions.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(extractions_with_spans.model_dump(), f, ensure_ascii=False, indent=2)

    print(f"✓ Results saved to: {output_file}")
    print()

    # Print sample results
    print("=" * 80)
    print("Sample Results:")
    print("=" * 80)
    print()

    if extractions_with_spans.tnm_classifications:
        print("TNM Classifications:")
        for idx, tnm in enumerate(extractions_with_spans.tnm_classifications[:3]):
            print(f"  {idx + 1}. {tnm.tnm_value} ({tnm.classification_type})")
            for span in tnm.spans[:1]:  # Show first span only
                print(f"     \"{span.text}\" at position {span.start_char}-{span.end_char}")
        print()

    if extractions_with_spans.hormone_receptors:
        print("Hormone Receptors:")
        for idx, receptor in enumerate(extractions_with_spans.hormone_receptors[:5]):
            print(f"  {idx + 1}. {receptor.receptor_type}: {receptor.value}")
            for span in receptor.spans[:1]:
                print(f"     \"{span.text[:50]}...\"")
        print()

    print("=" * 80)
    print("Test completed successfully!")
    print("=" * 80)


if __name__ == "__main__":
    main()
