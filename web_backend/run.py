from datetime import datetime, timedelta
import xml.etree.ElementTree as ET

import pandas as pd

from . import db
from .models import *
from llm_backend import LLMBackend, LLMBackendBase


def add_batch(patients: list[str], questions: list[Question]):
    bt = Batch(schedule=datetime.now()+timedelta(minutes=30), done=None)
    db.session.add(bt)
    db.session.flush()

    for patient_filename in patients:
        root = ET.parse(patient_filename)
        pacient = root.find('pacient')

        if pacient is not None:
            patient_id = pacient.get('id')

            bt_patient = BatchPatient(batch_id=bt.id, patient_id=patient_id)
            db.session.add(bt_patient)
            db.session.flush()

            for zaznam in pacient.findall('zaznam'):
                pdate = zaznam.find('datum')
                ptype = zaznam.find('typ')
                ptext = zaznam.find('text')
                if pdate is None or ptype is None or ptext is None:
                    continue
                pdate = datetime.strptime(pdate.text, '%Y-%m-%d')
                patient_record = PatientRecord(batch_patient_id=bt_patient.id, date=pdate, type=ptype.text, text=ptext.text)
                db.session.add(patient_record)

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
            'patent_id': patient.id,
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
                patient_record_id=patient.id,
                confidence=c['confidence'],
                record_id=c['record_id'],
                offset_start=c['start_char'],
                offset_end=c['end_char'],
            )
            db.session.add(finding)

        print(output)
        summary = backend.summarize_patient(input_data, output)
        print(summary)
        patients.append((input_data, output, summary))

    batch.summary = backend.summarize_batch(patients)
    batch.done = datetime.now()
    db.session.commit()
