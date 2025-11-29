from datetime import datetime
from . import db


class Question(db.Model):
    __tablename__ = 'questions'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String, nullable=False)
    description = db.Column(db.Text, nullable=False)
    # TODO


class Batch(db.Model):
    __tablename__ = 'batches'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    schedule = db.Column(db.DateTime, nullable=False, default=datetime.now)
    done = db.Column(db.DateTime, nullable=True, default=datetime.now)
    summary = db.Column(db.Text, nullable=True)


class BatchQuestion(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    batch_id = db.Column(
        db.Integer,
        db.ForeignKey('batches.id'),
        nullable=False
    )
    question_id = db.Column(
        db.Integer,
        db.ForeignKey('questions.id'),
        nullable=False
    )


class BatchPatient(db.Model):
    __tablename__ = 'batch_patients'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    batch_id = db.Column(
        db.Integer,
        db.ForeignKey('batches.id'),
        nullable=False
    )
    patient_id = db.Column(db.String, nullable=False)
    short_summary = db.Column(db.Text, nullable=True)
    long_summary = db.Column(db.Text, nullable=True)


class PatientRecord(db.Model):
    __tablename__ = 'patient_records'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    batch_patient_id = db.Column(
        db.Integer,
        db.ForeignKey('batch_patients.id'),
        nullable=False
    )
    date = db.Column(db.Date, nullable=False)
    type = db.Column(db.String, nullable=False)
    text = db.Column(db.Text, nullable=False)


class Finding(db.Model):
    __tablename__ = 'findings'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    patient_record_id = db.Column(
        db.Integer,
        db.ForeignKey('patient_records.id'),
        nullable=False
    )
    question_id = db.Column(
        db.Integer,
        db.ForeignKey('questions.id'),
        nullable=False
    )
    offset_start = db.Column(db.Integer)
    offset_end = db.Column(db.Integer)
