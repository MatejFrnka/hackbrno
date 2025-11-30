from datetime import datetime, timedelta
import xml.etree.ElementTree as ET
import difflib
import bisect
import time

import pandas as pd

from . import db
from .models import *
from llm_backend import LLMBackend, LLMBackendBase


def find_duplicates(value_text: str, ref_text: str, min_len=20):
    matcher = difflib.SequenceMatcher(None, value_text, ref_text)
    matches = matcher.get_matching_blocks()

    # Filter out trivial matches
    matches = [m for m in matches if m.size >= min_len]

    result = []
    for m in matches:
        result.append({
            'offset': m.a,
            'size': m.size,
            'offset_ref': m.b,
        })
    result.sort(key=lambda x: x['offset'])
    return result


def add_batch(patients: list[str], questions: list[Question], remove_duplicates=False):
    bt = Batch(schedule=datetime.now()+timedelta(minutes=30), done=None)
    db.session.add(bt)
    db.session.flush()

    for patient_filename in patients:
        root = ET.parse(patient_filename)
        pacient = root.find('pacient')

        if pacient is not None:
            patient_id = pacient.get('id')

            records = []

            bt_patient = BatchPatient(batch_id=bt.id, patient_id=patient_id)
            db.session.add(bt_patient)
            db.session.flush()

            for zaznam in pacient.findall('zaznam'):
                pdate = zaznam.find('datum')
                ptype = zaznam.find('typ')
                ptext = zaznam.find('text')
                if pdate is None or ptype is None or ptext is None:
                    continue
                patient_record = PatientRecord(
                    batch_patient_id=bt_patient.id,
                    date=datetime.strptime(pdate.text, '%Y-%m-%d'),
                    type=ptype.text,
                    text=ptext.text
                )
                records.append(patient_record)
                db.session.add(patient_record)
            db.session.flush()

            if remove_duplicates:
                records.sort(key=lambda x: x.date) # asc
                for i, record in enumerate(records):
                    all_text = ''
                    dividers = []
                    for cmp in records[:i]:
                        dividers.append(len(all_text))
                        all_text += cmp.text

                    removed = 0
                    for dup in find_duplicates(record.text, all_text):
                        offset_start = dup['offset'] - removed
                        size = dup['size']
                        record.text = record.text[:offset_start] + record.text[offset_start + size:]
                        removed += size
                        ref_i = bisect.bisect_left(dividers, dup['offset_ref']) - 1
                        ref_offset = dup['offset_ref'] - dividers[ref_i]

                        td = TextDuplicate(
                            patient_record_id=record.id,
                            was_at=offset_start,
                            duplicate_of=records[ref_i].id,
                            offset_start=ref_offset,
                            offset_end=ref_offset + size
                        )
                        db.session.add(td)

            db.session.flush()

    for q in questions:
        btq = BatchQuestion(batch_id=bt.id, question_id=q.id)
        db.session.add(btq)

    db.session.commit()


def process_batches():
    backend = LLMBackendBase()
    batches = Batch.query.where(Batch.done.is_(None)).all()
    for bt in batches:
        process_batch(bt, backend)


def patient_data(patient: BatchPatient):
    if patient is None:
        return pd.DataFrame()
    patient: BatchPatient
    records = []
    records_dict = dict()
    for rec in patient.records:
        records.append({
            'patient_id': patient.id,
            'record_id': rec.id,
            'date': rec.date,
            'type': rec.type,
            'text': rec.text,
        })
        records_dict[rec.id] = rec
    return pd.DataFrame(records), records_dict


def process_batch(batch: Batch, backend: LLMBackend):
    questions = []
    for q in batch.questions:
        questions.append((q.id, q.name, q.description))

    patients = []
    for patient in batch.patients:
        input_data, records = patient_data(patient)
        output = backend.process_patient(input_data, questions)
        for c in output['citations']:
            finding = Finding(
                patient_record_id=c['record_id'],
                question_id=c['question_id'],
                confidence=c['confidence'],
                offset_start=c['start_char'],
                offset_end=c['end_char'],
            )
            db.session.add(finding)
        for h in output['highlights']:
            highlight = Highlight(
                patient_record_id=h['record_id'],
                offset_start=h['start_char'],
                offset_end=h['end_char'],
                description=h['note'],
            )
            db.session.add(highlight)
        patient.long_summary = output['summary_long']
        patient.short_summary = output['summary_short']
        patients.append((patient.patient_id, output['summary_long']))

    batch.summary = backend.summarize_batch(patients)
    batch.done = datetime.now()
    db.session.commit()


def _load_existing_findings_as_dicts(patient: BatchPatient):
    """
    Load existing findings from database and convert to list of dicts.

    Args:
        patient: BatchPatient instance

    Returns:
        List of dicts with keys: {question_id, quoted_text, confidence, record_id, start_char, end_char}
    """
    findings_dicts = []

    # Iterate through patient's records and their findings
    for record in patient.records:
        for finding in record.findings:
            # Extract quoted text from record using offsets
            quoted_text = record.text[finding.offset_start:finding.offset_end]

            findings_dicts.append({
                'question_id': finding.question_id,
                'quoted_text': quoted_text,
                'confidence': finding.confidence,
                'record_id': finding.patient_record_id,
                'start_char': finding.offset_start,
                'end_char': finding.offset_end
            })

    return findings_dicts


def regenerate_patient_summary(patient_id: int):
    """
    Regenerate summaries for a single patient using existing findings.

    Args:
        patient_id: BatchPatient ID

    Returns:
        Dictionary with:
            - status: "success" or "error"
            - patient_id: Patient identifier
            - short_summary: HTML summary
            - long_summary: HTML summary
            - total_citations: Number of citations
            - processing_time_seconds: Float
            - error: Error message (if status="error")
    """
    start_time = time.time()

    backend = LLMBackendBase()
    # 1. Retrieve patient and validate
    patient = BatchPatient.query.get(patient_id)
    if patient is None:
        return {
            'status': 'error',
            'error': f'Patient with ID {patient_id} not found'
        }

    try:
        # 2. Load patient data
        input_data, records_dict = patient_data(patient)

        # 3. Load existing findings as dicts
        findings_dicts = _load_existing_findings_as_dicts(patient)

        # 4. Get batch questions
        batch = Batch.query.get(patient.batch_id)
        questions = [(q.id, q.name, q.description) for q in batch.questions]

        # 5. Call LLM backend to regenerate summaries
        result = backend.regenerate_patient_summaries(input_data, findings_dicts, questions)

        # 6. Update patient summaries
        patient.long_summary = result['summary_long']
        patient.short_summary = result['summary_short']

        # 7. Commit to database
        db.session.commit()

        # 8. Calculate processing time
        processing_time = time.time() - start_time

        # 9. Return success response
        return {
            'status': 'success',
            'patient_id': patient.patient_id,
            'short_summary': result['summary_short'],
            'long_summary': result['summary_long'],
            'total_citations': len(findings_dicts),
            'processing_time_seconds': round(processing_time, 2)
        }

    except Exception as e:
        # Rollback any database changes
        db.session.rollback()

        # Return error response
        return {
            'status': 'error',
            'error': str(e),
            'patient_id': patient.patient_id if patient else None
        }
