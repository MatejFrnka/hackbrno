from flask import Flask, jsonify, redirect
from flask_sqlalchemy import SQLAlchemy

from llm_backend import LLMBackend

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

from .models import *
from . import run


mock_questions = [
    (
        1,
        "Datum stanovení diagnózy",
        """
   - Datum, kdy byla poprvé stanovena diagnóza karcinomu prsu
   - Může být přímé ("5. října 2022") nebo odvozené z kontextu
   - Označ jako `inferred: true` pokud datum odvozuješ"""
    ),
    (
        2,
        "TNM klasifikace",
        """
   - Klinická klasifikace: cTNM (např. "cT2N0M0")
   - Patologická klasifikace: pTNM (např. "pT2 pN0(i−)(sn) M0")
   - Extrahuj všechny výskyty, i když se opakují"""
    ),
    (
        3,
        "Hormonální receptory",
        """
   - ER (estrogenové receptory): hodnoty v % nebo pozitivní/negativní
   - PR (progesteronové receptory): hodnoty v % nebo pozitivní/negativní
   - HER2: hodnoty jako "0", "negativní", "pozitivní"""
    ),
    (4,
        "Léčba mimo MOÚ",
        """
   - Zmínky o léčbě v jiné nemocnici nebo zdravotnickém zařízení
   - Je důležité vědět, jestli pacient absolvoval léčbu mimo MOÚ, hlavně před první návštěvou v MOÚ, případně mezi cykly systémové léčby.
   - Může jít o ambulance, regionální nemocnice, domácí péče mimo MOÚ"""
    ),
    (5,
        "Progrese",
        """
   - Informace o progresi/zhoršení onemocnění
   - Růst tumoru, nová ložiska, zhoršení stavu"""
    ),
    (6,
        "Recidiva",
        """
   - Zmínky o recidivě nebo návratu onemocnění
   - Lokální i vzdálená recidiva"""
    ),
    (7,
        "Vzdálené metastázy",
        """
   - Výskyt metastáz v různých lokacích
   - Játra, kosti, plíce, mozek, atd."""
    )
]


def seed_question(name: str, desc: str):
    db.session.add(Question(name=name, description=desc))


with app.app_context():
    DATA_DIR = 'data'
    db.create_all()

    if Question.query.count() == 0:
        for _, qn, qd in mock_questions:
            seed_question(qn, qd)
        db.session.commit()
        import os
        files = []
        for filename in os.listdir(DATA_DIR):
            if '.xml' not in filename:
                continue
            files.append(os.path.join(DATA_DIR, filename))
        run.add_batch(files, Question.query.all())


@app.route("/")
def home():
    questions = []
    for q in Question.query.all():
        questions.append({
            'id': q.id,
            'name': q.name,
            'description': q.description,
        })
    curr_batch = {}
    bt = current_batch()
    curr_batch['questions'] = []
    for q in bt.questions:
        curr_batch['questions'].append({
            'id': q.id,
            'name': q.name,
            'description': q.description,
        })
    return jsonify({'questions': questions, 'batch': curr_batch})


def current_batch() -> Batch:
    bt = Batch.query.where(Batch.done.isnot(None)).order_by(Batch.done.desc()).first()
    return bt


@app.route('/api/dashboard')
def dashboard_api():
    bt = current_batch()
    if bt is None:
        return jsonify({})
    patients = []
    for p in bt.patients:
        patients.append({
            'short_summary': p.short_summary,
            'long_summary': p.long_summary,
        })
    data = {
        'summary': bt.summary,
        'done': bt.done,
        'patients': patients,
    }
    return jsonify(data)


@app.route('/api/patient/<string:patient_id>')
def patient_api(patient_id: str):
    bt = current_batch()
    patient = BatchPatient.query.where(BatchPatient.batch_id == bt.id and BatchPatient.patient_id == patient_id).first()
    if patient is None:
        return jsonify({})
    # TODO
