# AI Medical Report Explainer & PHR Platform
 
A full-stack web app that lets a user upload a medical lab report (PDF), automatically extracts and structures the biomarker data, and generates plain-language AI explanations for any abnormal values — without diagnosing or recommending treatment. Users can view a consolidated health dashboard, track how specific biomarkers trend across multiple reports over time, and ask questions about their own reports through an AI chat assistant.
 
## Tech Stack
 
- **Backend:** Python, FastAPI, PostgreSQL (Neon), SQLAlchemy, JWT auth
- **Frontend:** React, TypeScript, Vite
- **AI:** Google Gemini API for explanations, summaries, and trend/chat responses
- **PDF Processing:** PyMuPDF for text extraction
## Project Structure
 
```
backend/         FastAPI backend (auth, upload, dashboard, trends, chat)
bolt-frontend/   React frontend
```
 
## Running Locally
 
**Backend**
```
cd backend
pip install -r requirements.txt --break-system-packages
uvicorn app.main:app --reload
```
 
**Frontend**
```
cd bolt-frontend
npm install
npm run dev
```
 
Set `DATABASE_URL`, `SECRET_KEY`, and `GEMINI_API_KEY` in `backend/.env`, and the API base URL in `bolt-frontend/.env`.
 
## Disclaimer
 
This platform is an educational/organizational tool. It does not diagnose conditions or recommend treatment — always consult a qualified healthcare professional for abnormal findings.
