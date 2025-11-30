# Medical Patient Management System

AI-powered medical document processing system for extracting structured information from patient records.

## Overview

This system processes medical documents using LLM-based extraction to identify medical findings, answer clinical questions, and generate patient summaries. It features a web-based dashboard for reviewing patients and their medical documentation.

## Architecture

- **Frontend**: React + Vite application with patient selection and detailed document viewer
- **Backend**: Flask REST API with SQLite database
- **LLM Processing**: OpenAI-based extraction pipeline for medical information
- **FHIR Integration**: FHIR R4 resource processing and code standardization

## Features

- **Automated Document Processing**: Batch processing of FHIR XML medical records
- **Intelligent Extraction**: LLM-driven extraction of medical findings with confidence scoring
- **Question Answering**: Configurable medical questions answered from patient data
- **Patient Summaries**: Auto-generated short and long-form patient summaries
- **Highlight System**: Visual highlighting of relevant text passages in documents
- **Multi-language Support**: i18n support in the frontend
- **Docker Deployment**: Complete containerized setup

## Prerequisites

- Docker and Docker Compose
- OpenAI API key or compatible endpoint
- Python 3.12+
- Node.js 18+ (for local development)

## Quick Start

1. **Configure environment**:
```bash
cp .env.example .env
# Edit .env and add your OpenAI API credentials
```

2. **Start with Docker**:
```bash
docker-compose up
```

3. **Access the application**:
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:5001

## Environment Variables

```env
OPENAI_API_KEY=your-openai-api-key-here
OPENAI_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-5.1
```

## Project Structure

```
├── frontend/               # React frontend application
│   ├── src/
│   │   ├── components/    # Reusable UI components
│   │   ├── pages/         # Page components
│   │   ├── services/      # API service layer
│   │   ├── i18n/          # Internationalization
│   │   └── utils/         # Utility functions
│   └── index.html
├── web_backend/           # Flask REST API
│   ├── __init__.py        # API routes and CORS setup
│   ├── models.py          # SQLAlchemy database models
│   └── run.py             # Batch processing orchestration
├── llm_backend/           # LLM extraction pipeline
│   └── backend.py         # Feature extraction and summarization
├── llm_extraction/        # Core extraction logic
├── data/                  # Patient medical records (FHIR XML)
├── fhir.py               # FHIR resource processing
├── docker-compose.yml    # Container orchestration
└── requirements.txt      # Python dependencies
```

## API Endpoints

- `GET /api/dashboard` - Dashboard data with all patients
- `GET /api/patient/<id>` - Detailed patient information
- `GET /api/patient/<id>/regenerate-summary` - Regenerate patient summaries
- `GET /api/process` - Trigger batch processing

## Development

### Local Backend Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run Flask development server
cd web_backend
python run.py
```

### Local Frontend Development

```bash
cd frontend
npm install
npm run dev
```

## Database Models

- **Question**: Medical questions to answer from patient data
- **Batch**: Processing batches with summary
- **BatchPatient**: Patient records within a batch
- **MedicalRecord**: Individual medical documents
- **Finding**: Extracted medical findings linked to questions
- **Highlight**: Annotated text spans in documents

## FHIR Integration

The system can process FHIR R4 resources and standardize medical codes using a CSV-based code mapping system. FHIR resources are sent to a configurable FHIR server endpoint.

## Data Processing Flow

1. XML documents are loaded from `data/` directory
2. LLM extracts relevant information based on configured questions
3. Findings are matched to exact text spans using span matching
4. Patient summaries are generated from extracted findings
5. Batch summary aggregates information across all patients
6. Results are stored in SQLite database and served via API
