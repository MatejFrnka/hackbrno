from datetime import datetime, timedelta
import xml.etree.ElementTree as ET

import pandas as pd

from . import db
from .models import *
from llm_backend import LLMBackend


def add_batch(patients: list[str]):
    import pandas as pd

    # TODO: add questions
    # TODO: add schedule
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

    db.session.commit()


def process_batches():
    backend = LLMBackend()
    batches = Batch.query.where(Batch.done is None).all()
    for bt in batches:
        process_batch(bt, backend)


def patient_data(batch_id, patient_id):
    patient = BatchPatient.query.where(BatchPatient.batch_id == batch_id and BatchPatient.patient_id == patient_id).first()
    if patient is None:
        return pd.DataFrame()



def process_batch(batch: Batch, backend: LLMBackend):
    pass
