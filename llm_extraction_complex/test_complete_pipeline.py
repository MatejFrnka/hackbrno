"""
Test script for complete medical information extraction pipeline.

Tests the full workflow on HACK01.xml including:
- Feature extraction
- Span calculation
- Semantic deduplication
- Inconsistency detection
- Timeline generation
- JSON output formatting
"""

from dotenv import load_dotenv
from llm_extraction_complex.backend import LLMBackend


def main():
    # Load environment variables
    load_dotenv()

    print("=" * 80)
    print("Complete Medical Information Extraction Pipeline - Test Run")
    print("=" * 80)
    print()

    # Initialize backend
    print("Initializing LLM Backend...")
    backend = LLMBackend(model="gpt-4o-2024-08-06", extraction_mode="auto")
    print("✓ Backend initialized")
    print()

    # Process single patient file
    results = backend.process_patient_file(
        xml_path="data/HACK01.xml",
        output_path="output/HACK01_complete_results.json",
        save_output=True
    )

    print()
    print("=" * 80)
    print("Test completed successfully!")
    print("=" * 80)


if __name__ == "__main__":
    main()
