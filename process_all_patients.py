"""
Process all patient files with the complete extraction pipeline.

Processes all XML files in the data/ directory through:
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
    print("Medical Information Extraction - Process All Patients")
    print("=" * 80)
    print()

    # Initialize backend
    print("Initializing LLM Backend...")
    backend = LLMBackend(model="gpt-4o-2024-08-06", extraction_mode="auto")
    print("✓ Backend initialized")
    print()

    # Process all patients
    all_results = backend.process_all_patients(
        data_dir="data",
        output_dir="output"
    )

    print()
    print("=" * 80)
    print("All Processing Complete!")
    print("=" * 80)
    print(f"Successfully processed {len(all_results)} patients")
    print()


if __name__ == "__main__":
    main()
