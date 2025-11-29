from flask import Flask, jsonify, redirect
from flask_sqlalchemy import SQLAlchemy

from llm_backend import LLMBackend

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

from .models import *

with app.app_context():
    db.create_all()


@app.route("/")
def home():
    batches = []
    for bt in Batch.query.all():
        bt: Batch
        batches.append({
            'id': bt.id,
            'schedule': bt.schedule
        })
    return jsonify(batches)


def current_batch() -> Batch:
    bt = Batch.query.where(Batch.done.isnot(None)).order_by(Batch.done.desc()).first()
    return bt


@app.route('/api/dashboard')
def dashboard_api():
    bt = current_batch()
    if bt is None:
        return jsonify({})
    # TODO: patients
    data = {
        'summary': bt.summary,
        'done': bt.done
    }
    return jsonify(data)


@app.route('/api/patient/<string:patient_id>')
def patient_api(patient_id: str):
    bt = current_batch()
    patient = BatchPatient.query.where(BatchPatient.batch_id == bt.id and BatchPatient.patient_id == patient_id).first()
    if patient is None:
        return jsonify({})
    # TODO


from .run import add_batch


@app.route('/add')
def _add_b():
    import os
    files = []
    for filename in os.listdir('data'):
        if '.xml' not in filename:
            continue
        files.append(os.path.join('data', filename))
    add_batch(files)
    return redirect('home')
