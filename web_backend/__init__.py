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


# Enable CORS only for API routes
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response


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
                'description': q.description,
                'rgb_color': q.rgb_color,
                'documents_count': question_document_count.get(q.id, 0),
            } for q in batch_questions 
            if q.id in answered_question_ids
        ]
        unanswered_questions = [
            {
                'id': q.id,
                'description': q.description,
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
        'documents_total': sum(p.documents_total for p in patients),
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
            'description': q.description,
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
