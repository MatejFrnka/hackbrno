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

from data import mock_questions


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
    origin = 'http://localhost:5173'
    response.headers.add('Access-Control-Allow-Origin', origin)
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

        difficulty = len(answered_questions) / (len(answered_questions) + len(unanswered_questions))
        difficulty = round(5 * difficulty)

        patients.append({
            'id': p.id,
            'name': p.patient_id,
            'short_summary': p.short_summary,
            'documents_total': len(p.records),
            'relevant_documents_total': sum(1 for r in p.records if len(r.findings) > 0),
            'documents_start_date': min(r.date for r in p.records),
            'documents_end_date': max(r.date for r in p.records),
            'difficulty': difficulty,
            'answered_questions': answered_questions,
            'unanswered_questions': unanswered_questions,
        })
    data = {
        'summary': bt.summary,
        'patients': patients,
        'documents_total': sum(p['documents_total'] for p in patients),
    }
    return jsonify(data)


@app.route('/api/patient/<int:patient_id>')
def patient_api(patient_id: int):
    bt = current_batch()
    patient = BatchPatient.query.where(BatchPatient.id == patient_id and BatchPatient.batch_id == bt.id).first()
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
        commented_highlights = []
        for highlight in record.highlights:
            print(highlight)
            commented_highlights.append({
                'offset_start': highlight.offset_start,
                'offset_end': highlight.offset_end,
                'description': highlight.description,
            })
        
        documents.append({
            'id': record.id,
            'date': record.date.isoformat() if record.date else None,
            'type': record.type,
            'text': record.text,
            'highlights': highlights,
            'commented_highlights': commented_highlights,
        })
    
    # Sort documents by date
    documents.sort(key=lambda d: d['date'] if d['date'] else '')
    
    return jsonify({
        'name': patient.patient_id, 
        'long_summary': patient.long_summary,
        'questions_types': questions,
        'documents': documents,
    })

