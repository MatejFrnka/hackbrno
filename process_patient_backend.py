#!/usr/bin/env python3
"""
Script to process a single patient using LLMBackendBase and save results to JSON.

Usage:
    python process_patient.py HACK03 --output output/HACK03_processed.json
"""

import argparse
import json
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

from llm_backend.backend import LLMBackendBase
from data.mock_data import mock_questions

# Define extraction questions
QUESTIONS = mock_questions


def load_patient_data(patient_id: str, csv_path: str = "data/records.csv") -> pd.DataFrame:
    """
    Load patient data from CSV file.
    
    Args:
        patient_id: Patient ID (e.g., "HACK03")
        csv_path: Path to the CSV file with patient records
        
    Returns:
        DataFrame with patient records
    """
    df = pd.read_csv(csv_path)
    patient_df = df[df['patient_id'] == patient_id].copy()
    
    if patient_df.empty:
        raise ValueError(f"Patient {patient_id} not found in {csv_path}")
    
    print(f"Loaded {len(patient_df)} records for patient {patient_id}")
    return patient_df


def process_patient(patient_id: str, csv_path: str = "data/records.csv") -> dict:
    """
    Process a patient using LLMBackendBase.
    
    Args:
        patient_id: Patient ID (e.g., "HACK03")
        csv_path: Path to the CSV file with patient records
        
    Returns:
        Dictionary with processed results
    """
    # Load patient data
    patient_df = load_patient_data(patient_id, csv_path)
    
    # Initialize backend
    print("\nInitializing LLM backend...")
    backend = LLMBackendBase()
    
    # Process patient
    print(f"\nProcessing patient {patient_id}...")
    result = backend.process_patient(patient_df, QUESTIONS)
    
    print(f"\n✓ Processing complete!")
    print(f"  - Total citations: {result['total_citations']}")
    print(f"  - Total highlights: {len(result['highlights'])}")
    print(f"  - Summary length: {len(result['summary_long'])} characters")
    
    return result


def save_results(result: dict, output_path: str):
    """
    Save results to JSON file.
    
    Args:
        result: Processing results dictionary
        output_path: Path to output JSON file
    """
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"\n✓ Results saved to: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Process a patient using LLMBackendBase and save results to JSON"
    )
    parser.add_argument(
        "--patient_id",
        help="Patient ID (e.g., HACK03)"
    )
    parser.add_argument(
        "--csv",
        default="data/records.csv",
        help="Path to CSV file with patient records (default: data/records.csv)"
    )
    parser.add_argument(
        "--output",
        help="Output JSON file path (default: output/{patient_id}_processed.json)"
    )
    
    args = parser.parse_args()
    
    # Set default output path if not provided
    output_path = args.output or f"output/{args.patient_id}_processed.json"
    
    try:
        # Process patient
        result = process_patient(args.patient_id, args.csv)
        
        # Save results
        save_results(result, output_path)
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
