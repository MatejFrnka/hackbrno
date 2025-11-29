"""
XML parser for Czech medical records.

Parses patient XML files and performs exact duplicate removal based on text hashing.
"""

import hashlib
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List
from .models import MedicalRecord, PatientData


class XMLParser:
    """Parser for Czech medical record XML files"""

    def parse_patient_file(self, xml_path: str) -> PatientData:
        """
        Parse a patient XML file and extract all medical records.

        Args:
            xml_path: Path to XML file (e.g., "data/HACK01.xml")

        Returns:
            PatientData with deduplicated records
        """
        # Parse XML
        tree = ET.parse(xml_path)
        root = tree.getroot()

        # Extract patient ID
        pacient = root.find('.//pacient')
        if pacient is None:
            raise ValueError(f"No <pacient> element found in {xml_path}")

        patient_id = pacient.get('id')
        if not patient_id:
            raise ValueError(f"Patient element missing 'id' attribute in {xml_path}")

        # Extract all records
        records = []
        seen_hashes = set()
        duplicate_count = 0

        for idx, zaznam in enumerate(pacient.findall('zaznam')):
            # Extract fields
            datum_elem = zaznam.find('datum')
            typ_elem = zaznam.find('typ')
            text_elem = zaznam.find('text')

            # Validate required fields
            if datum_elem is None or typ_elem is None or text_elem is None:
                print(f"Warning: Skipping incomplete record {idx} in {patient_id}")
                continue

            date = datum_elem.text or ""
            record_type = typ_elem.text or ""
            text = text_elem.text or ""

            # Calculate hash for deduplication
            text_hash = hashlib.sha256(text.encode('utf-8')).hexdigest()

            # Check for exact duplicate
            if text_hash in seen_hashes:
                duplicate_count += 1
                print(f"Duplicate found in {patient_id} at index {idx} (date: {date})")
                continue

            seen_hashes.add(text_hash)

            # Create record
            record = MedicalRecord(
                record_id=f"{patient_id}_{len(records)}",
                patient_id=patient_id,
                date=date,
                record_type=record_type,
                text=text,
                text_hash=text_hash
            )
            records.append(record)

        # Sort records chronologically
        records.sort(key=lambda r: r.date)

        # Re-assign record IDs after sorting
        for idx, record in enumerate(records):
            record.record_id = f"{patient_id}_{idx}"

        print(f"Parsed {patient_id}: {len(records)} unique records ({duplicate_count} duplicates removed)")

        return PatientData(
            patient_id=patient_id,
            records=records,
            duplicate_count=duplicate_count
        )

    def get_record_by_id(self, patient_data: PatientData, record_id: str) -> MedicalRecord:
        """
        Get a specific record by ID.

        Args:
            patient_data: Patient data containing records
            record_id: Record ID to find

        Returns:
            MedicalRecord if found

        Raises:
            ValueError if record not found
        """
        for record in patient_data.records:
            if record.record_id == record_id:
                return record
        raise ValueError(f"Record {record_id} not found in patient {patient_data.patient_id}")
