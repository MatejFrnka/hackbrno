"""
Main LLM Backend orchestrator.

Coordinates all components to process patient files end-to-end.
"""

import os
import json
from typing import Dict, Any, Literal
from openai import OpenAI
from .xml_parser import XMLParser
from .extractor import FeatureExtractor
from .span_calculator import SpanCalculator
from .deduplicator import SemanticDeduplicator
from .inconsistency_detector import InconsistencyDetector
from .timeline_generator import TimelineGenerator
from .output_formatter import OutputFormatter


class LLMBackend:
    """
    Main backend orchestrator for medical information extraction pipeline.

    Processes patient XML files through complete pipeline:
    1. Parse XML and remove duplicates
    2. Extract features with LLM
    3. Calculate character spans
    4. Semantic deduplication
    5. Inconsistency detection
    6. Timeline generation
    7. Format JSON output
    """

    def __init__(self,
                 api_key: str = None,
                 model: str = "gpt-4o-2024-08-06",
                 extraction_mode: Literal["auto", "bulk", "per_record"] = "auto"):
        """
        Initialize LLM Backend.

        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            model: Model to use for all LLM operations
            extraction_mode: Extraction mode (auto/bulk/per_record)
        """
        # Load API key
        if api_key is None:
            api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment")

        # Initialize OpenAI client
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.extraction_mode = extraction_mode

        # Initialize all components
        self.xml_parser = XMLParser()
        self.extractor = FeatureExtractor(self.client, model=model)
        self.span_calculator = SpanCalculator()
        self.deduplicator = SemanticDeduplicator(self.client, model=model)
        self.inconsistency_detector = InconsistencyDetector(self.client, model=model)
        self.timeline_generator = TimelineGenerator(self.client, model=model)
        self.output_formatter = OutputFormatter()

    def process_patient_file(self,
                            xml_path: str,
                            output_path: str = None,
                            save_output: bool = True) -> Dict[str, Any]:
        """
        Process a single patient XML file through complete pipeline.

        Args:
            xml_path: Path to patient XML file
            output_path: Optional custom output path (defaults to output/{patient_id}_results.json)
            save_output: Whether to save JSON output to file

        Returns:
            Complete results dictionary
        """
        print("=" * 80)
        print(f"Processing: {xml_path}")
        print("=" * 80)
        print()

        # Step 1: Parse XML
        print("[1/7] Parsing XML file...")
        patient_data = self.xml_parser.parse_patient_file(xml_path)
        print(f"✓ Patient ID: {patient_data.patient_id}")
        print(f"  - Records: {len(patient_data.records)}")
        print(f"  - Duplicates removed: {patient_data.duplicate_count}")
        print()

        # Step 2: Extract features
        print("[2/7] Extracting features with LLM...")
        extractions = self.extractor.extract_features(patient_data, mode=self.extraction_mode)
        print()

        # Step 3: Calculate spans
        print("[3/7] Calculating character spans...")
        extractions_with_spans = self.span_calculator.calculate_all_spans(extractions, patient_data)
        print(f"✓ Calculated spans for all extractions")
        self._print_extraction_summary(extractions_with_spans)
        print()

        # Step 4: Semantic deduplication
        print("[4/7] Performing semantic deduplication...")
        deduplication = self.deduplicator.deduplicate_extractions(extractions_with_spans)
        print()

        # Step 5: Inconsistency detection
        print("[5/7] Detecting medical inconsistencies...")
        inconsistencies = self.inconsistency_detector.detect(extractions_with_spans, patient_data)
        print()

        # Step 6: Timeline generation
        print("[6/7] Generating patient timeline...")
        timeline = self.timeline_generator.generate(extractions_with_spans, patient_data)
        print()

        # Step 7: Format output
        print("[7/7] Formatting final output...")
        results = self.output_formatter.format_output(
            patient_data=patient_data,
            extractions=extractions_with_spans,
            deduplication=deduplication,
            inconsistencies=inconsistencies,
            timeline=timeline
        )
        print("✓ Output formatted")
        print()

        # Save to file
        if save_output:
            if output_path is None:
                output_dir = "output"
                os.makedirs(output_dir, exist_ok=True)
                output_path = f"{output_dir}/{patient_data.patient_id}_results.json"

            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)

            print(f"✓ Results saved to: {output_path}")
            print()

        # Print summary
        self._print_final_summary(results)

        return results

    def process_all_patients(self,
                            data_dir: str = "data",
                            output_dir: str = "output") -> Dict[str, Dict[str, Any]]:
        """
        Process all patient XML files in a directory.

        Args:
            data_dir: Directory containing patient XML files
            output_dir: Directory to save output files

        Returns:
            Dictionary mapping patient IDs to results
        """
        print("=" * 80)
        print("Processing All Patient Files")
        print("=" * 80)
        print()

        # Find all XML files
        xml_files = sorted([f for f in os.listdir(data_dir) if f.endswith('.xml')])
        print(f"Found {len(xml_files)} patient files")
        print()

        # Create output directory
        os.makedirs(output_dir, exist_ok=True)

        # Process each file
        all_results = {}
        for idx, xml_file in enumerate(xml_files, 1):
            print(f"\n{'=' * 80}")
            print(f"Patient {idx}/{len(xml_files)}: {xml_file}")
            print(f"{'=' * 80}\n")

            try:
                xml_path = os.path.join(data_dir, xml_file)
                output_path = os.path.join(output_dir, xml_file.replace('.xml', '_results.json'))

                results = self.process_patient_file(
                    xml_path=xml_path,
                    output_path=output_path,
                    save_output=True
                )

                patient_id = results['metadata']['patient_id']
                all_results[patient_id] = results

            except Exception as e:
                print(f"ERROR: Failed to process {xml_file}: {e}")
                continue

        # Print overall summary
        print("\n" + "=" * 80)
        print("All Patients Processed")
        print("=" * 80)
        print(f"Successfully processed: {len(all_results)}/{len(xml_files)} patients")
        print()

        return all_results

    def _print_extraction_summary(self, extractions):
        """Print summary of extractions"""
        print(f"  - Diagnosis dates: {len(extractions.diagnosis_dates)}")
        print(f"  - TNM classifications: {len(extractions.tnm_classifications)}")
        print(f"  - Hormone receptors: {len(extractions.hormone_receptors)}")
        print(f"  - External treatments: {len(extractions.external_treatments)}")
        print(f"  - Progressions: {len(extractions.progressions)}")
        print(f"  - Recurrences: {len(extractions.recurrences)}")
        print(f"  - Metastases: {len(extractions.metastases)}")

    def _print_final_summary(self, results: Dict[str, Any]):
        """Print final processing summary"""
        print("=" * 80)
        print("Processing Summary")
        print("=" * 80)
        print(f"Patient ID: {results['metadata']['patient_id']}")
        print(f"Records processed: {results['metadata']['num_records']}")
        print()

        print("Extractions:")
        for feature, count in results['extractions']['counts'].items():
            print(f"  - {feature}: {count}")
        print()

        print("Deduplication:")
        print(f"  - Duplicate groups found: {results['deduplication']['summary']['total_groups']}")
        print()

        print("Inconsistencies:")
        print(f"  - Total: {results['inconsistencies']['summary']['total']}")
        if results['inconsistencies']['summary']['total'] > 0:
            print(f"  - Critical: {results['inconsistencies']['summary']['by_severity']['critical']}")
            print(f"  - Moderate: {results['inconsistencies']['summary']['by_severity']['moderate']}")
            print(f"  - Minor: {results['inconsistencies']['summary']['by_severity']['minor']}")
        print()

        print("Timeline:")
        print(f"  - Overall narrative: {len(results['timeline']['overall_narrative'])} characters")
        print("=" * 80)
