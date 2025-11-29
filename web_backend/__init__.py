from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy

from llm_backend import LLMBackend

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

from .models import *

with app.app_context():
    db.create_all()

with app.app_context():
    bt = Batch()
    db.session.add(bt)
    db.session.commit()

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