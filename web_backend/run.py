from datetime import datetime, timedelta
import xml.etree.ElementTree as ET
import difflib
import bisect

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
        # TODO: process highlights
        # summary = backend.summarize_patient(input_data, output)
        patients.append((input_data, output, '', ''))

    # batch.summary = backend.summarize_batch(patients)
    batch.done = datetime.now()
    db.session.commit()
