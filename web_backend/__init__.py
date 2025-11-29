from dotenv import load_dotenv
load_dotenv()

from flask import Flask, jsonify, redirect
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

from .models import *
from . import run

questions_colors = [
    "#FF6B6B",  # vibrant coral red
    "#4ECDC4",  # teal / aquamarine
    "#5567FF",  # strong periwinkle blue
    "#FFD93D",  # warm golden yellow
    "#6A4C93",  # purple grape
    "#1A9E7D",  # emerald green
    "#FF8E3C",  # vivid orange
    "#00A8E8",  # bright sky blue
    "#D7263D",  # crimson rose
    "#3EC300"   # neon green
]

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


def seed_question(name: str, desc: str, color: str):
    db.session.add(Question(name=name, description=desc, rgb_color=color))


with app.app_context():
    DATA_DIR = 'data'
    db.create_all()

    if Question.query.count() == 0:
        for i, (_, qn, qd) in enumerate(mock_questions):
            seed_question(qn, qd, questions_colors[i])
        db.session.commit()
        import os
        files = []
        for filename in os.listdir(DATA_DIR):
            if '.xml' not in filename:
                continue
            files.append(os.path.join(DATA_DIR, filename))
        run.add_batch(files, Question.query.all())


# Enable CORS only for API routes
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', 'http://localhost:5173')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response


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


@app.route('/api/process')
def process_api():
    run.process_batches()
    return redirect('/')


@app.route('/api/dashboard')
def dashboard_api():
    bt = current_batch()
    if bt is None:
        return jsonify({}), 500
    
    # Get all questions from batch
    batch_questions = bt.questions
    
    patients = []
    for p in bt.patients:
        # Get all findings for this patient across all records
        answered_question_ids = set()
        # Count documents per question
        question_document_count = {}
        for record in p.records:
            question_ids_in_record = set()
            for finding in record.findings:
                question_id = finding.question_id
                answered_question_ids.add(question_id)
                question_ids_in_record.add(question_id)
            # Count this record for each question found in it
            for question_id in question_ids_in_record:
                question_document_count[question_id] = question_document_count.get(question_id, 0) + 1
        
        # Create lists of answered and unanswered question texts
        answered_questions = [
            {
                'id': q.id,
                'name': q.name,
                'rgb_color': q.rgb_color,
                'documents_count': question_document_count.get(q.id, 0),
            } for q in batch_questions 
            if q.id in answered_question_ids
        ]
        unanswered_questions = [
            {
                'id': q.id,
                'name': q.name,
                'rgb_color': q.rgb_color,
            } for q in batch_questions 
            if q.id not in answered_question_ids
        ]
        
        patients.append({
            'id': p.id,
            'short_summary': p.short_summary,
            'documents_total': len(p.records),
            'relevant_documents_total': sum(1 for r in p.records if len(r.findings) > 0),
            'documents_start_date': min(r.date for r in p.records),
            'documents_end_date': max(r.date for r in p.records),
            'difficulty': 2, # todo: compute difficulty
            'answered_questions': answered_questions,
            'unanswered_questions': unanswered_questions,
        })
    data = {
        'summary': bt.summary,
        'patients': patients,
        'documents_total': sum(p['documents_total'] for p in patients),
    }
    return jsonify(data)


@app.route('/api/patient/<string:patient_id>')
def patient_api(patient_id: str):
    bt = current_batch()
    patient = BatchPatient.query.where(BatchPatient.batch_id == bt.id and BatchPatient.patient_id == patient_id).first()
    if patient is None:
        return jsonify({}), 404

    # Get all questions from batch
    questions = [
        {
            'id': q.id,
            'name': q.name,
            'rgb_color': q.rgb_color,
        }
        for q in bt.questions
    ]
    
    # Get all documents with highlights
    documents = []
    for record in patient.records:
        highlights = []
        for finding in record.findings:
            # Get question info for this finding
            highlights.append({
                'question_id': finding.question_id,
                'offset_start': finding.offset_start,
                'offset_end': finding.offset_end,
            })
        
        documents.append({
            'id': record.id,
            'date': record.date.isoformat() if record.date else None,
            'type': record.type,
            'text': record.text,
            'highlights': highlights,
        })
    
    # Sort documents by date
    documents.sort(key=lambda d: d['date'] if d['date'] else '')
    
    return jsonify({
        'long_summary': patient.long_summary,
        'questions_types': questions,
        'documents': documents,
    })

