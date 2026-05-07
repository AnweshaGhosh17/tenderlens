# 🔍 TenderLens
**AI-Powered Bid Evaluation & Eligibility Intelligence for Government Procurement**

Built for AI Hackathon · Powered by Claude AI

---

## What It Does
TenderLens automates government tender evaluation. Upload a tender document and bidder submissions — TenderLens extracts all eligibility criteria, evaluates each bidder criterion-by-criterion, and produces an auditable matrix with source evidence for every verdict.

**Key Features:**
- Extracts eligibility criteria from any tender PDF automatically
- Evaluates bidder documents with explainable verdicts
- Detects conflicts/contradictions within tender documents
- Flags appeal risk on ambiguous disqualifications
- Scores document quality (handles scanned/photographed PDFs)
- Interactive comparison matrix with click-through evidence
- Exports signed-off procurement report

---


## Setup Instructions

### 1. Clone the repo
```bash
git clone https://github.com/YOUR_USERNAME/tenderlens.git
cd tenderlens
```

### 2. Create virtual environment
```bash
python -m venv venv
source venv/bin/activate      # Mac
venv\Scripts\activate         # Windows
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Add your API key
```bash
cp .env.example .env
# Open .env and paste your Anthropic API key
```

### 5. Run the app
```bash
uvicorn main:app --reload
```

Open your browser at: **http://localhost:8000**

---

## Project Structure
```
tenderlens/
├── .env                  ← Your API key (never commit this)
├── .env.example          ← Safe template for teammates
├── .gitignore
├── requirements.txt
├── main.py               ← FastAPI server (Person B)
├── ai_engine.py          ← Claude API calls (Person A)
├── pdf_utils.py          ← PDF processing (Person A)
├── uploads/              ← Uploaded files (auto-created)
└── frontend/
    └── index.html        ← Full UI (Person C)
```

---

## Daily Git Workflow
```bash
# Before starting work
git pull origin main

# After coding
git add YOUR_FILE
git commit -m "describe what you did"
git push origin main
```
