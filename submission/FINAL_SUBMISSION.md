# Capabl Agentic AI Final Project Submission — Track A (Essential)

## 1. Project Information

- **Project Name:** Cognivora AI — Educational Content Generator AI Agent
- **Track Selected:** **Track A (Essential)** with React Frontend Enhancement
- **Domain:** Educational Technology & Agentic Personalized Learning
- **Repository (GitHub):** [https://github.com/varun16-dev/Cognivora-AI](https://github.com/varun16-dev/Cognivora-AI)
- **Live Frontend (Vercel):** [https://cognivora-ai.vercel.app](https://cognivora-ai.vercel.app)
- **Live Backend (Render):** [https://cognivora-backend.onrender.com](https://cognivora-backend.onrender.com)
- **Swagger API Docs:** [https://cognivora-backend.onrender.com/docs](https://cognivora-backend.onrender.com/docs)

---

## 2. Team Members & Roles

| Member Name | Role & Specialization | Key Project Contributions |
| :--- | :--- | :--- |
| **Varun D** | Team Lead & AI Integration | Multi-agent orchestration, LangChain educational tools, Gemini API prompt engineering, RAG pipeline integration. |
| **Sindhuja S** | Frontend & UI/UX Engineering | React 19 + Vite dashboard, KaTeX LaTeX equation rendering, Lucide icons, Web Speech audio player UI, Recharts analytics. |
| **Mohith S** | Backend & Database Engineering | FastAPI asynchronous endpoints, SQLite SQLAlchemy models, PyMuPDF & python-docx parsers, Pytest automated testing suite. |

---

## 3. Project Abstract

**Cognivora AI** is an autonomous multi-agent educational assistant designed to bridge the gap between static academic materials and active, retained learning. Conventional study workflows force students to passively consume hundreds of pages of textbooks or use generic AI chatbots prone to out-of-syllabus hallucinations.

Cognivora AI solves this by deploying a collaborative multi-agent architecture built on FastAPI, Google Gemini, and ChromaDB:
1. **Document Agent** ingests PDFs, DOCX, and TXT files, extracting hierarchical curriculum outlines and indexing content into vector space with strict document boundaries.
2. **Coordinator Agent** classifies student queries into educational intents and routes them to specialized agents.
3. **Quiz Agent** generates calibrated, non-repetitive diagnostic assessments across Easy, Medium, and Hard tiers with strict anti-hallucination validation and exact page citations.
4. **Flashcard & Summary Agents** produce interactive spaced-repetition decks and 5 pedagogical digest modes.
5. **Adaptive Learning Engine** continuously calculates topic mastery via Exponentially Weighted Moving Averages (EWMA), alerting students to weak concepts (<60%) and recommending targeted review pathways.

---

## 4. Technology Stack

- **Frontend:** React 19, Vite 6, Tailwind CSS 4, React Router 7, Recharts, Lucide React, KaTeX (LaTeX math rendering via remark-math & rehype-katex), Browser Web Speech API.
- **Backend:** Python 3.11+, FastAPI, Uvicorn, LangChain, Pydantic v2, SQLAlchemy, ChromaDB, PyMuPDF (fitz), python-docx.
- **Artificial Intelligence:** Google Gemini API (`gemini-3.1-flash-lite`, `gemini-3.5-flash-lite`, `gemini-2.5-flash`), FastCurriculumEmbedder / Cosine vector similarity.
- **Persistence:** SQLite (`cognivora.db`), ChromaDB persistent storage.
- **Hosting & DevOps:** Render (Backend Cloud Web Service), Vercel (Edge Frontend CDN), GitHub CI.

---

## 5. Verified Track A Feature Audit

| Feature | Track A Requirement | Implementation Details | Status |
| :--- | :--- | :--- | :--- |
| **Document Upload & Parsing** | Support PDF, DOCX, TXT | PyMuPDF + python-docx + UTF-8 TXT parser with magic byte validation and error boundaries | **VERIFIED** |
| **Document-Grounded RAG** | Vector retrieval strictly bounded to document | ChromaDB with metadata filtering (`where={"document_id": doc_id}`) and cosine similarity fallback | **VERIFIED** |
| **AI Study Assistant** | Grounded Q&A with real citations | Coordinator agent with 4 pedagogical modes (Standard, Explain Simply, Exam Cram, Deep Dive) and page citations | **VERIFIED** |
| **Quiz Generator** | Easy, Medium, Hard tiers | Multi-stage difficulty validation enforcing Bloom's taxonomy: Easy (recall), Medium ($\ge 70\%$ applied), Hard ($\ge 80\%$ multi-step scenarios) | **VERIFIED** |
| **Question Types** | MCQs, True/False, Fill-in-Blank | Supported across API and UI; Hard mode strictly enforces scenario MCQs to prevent 50/50 guessing | **VERIFIED** |
| **Anti-Repetition Engine** | No repeated questions in consecutive quizzes | Jaccard token similarity ($\text{threshold} \ge 0.55$) against SQLite quiz history and intra-quiz deduplication | **VERIFIED** |
| **Quiz Grading & Feedback** | Instant scoring with review | Instant percentage calculation, question evaluation, pedagogical explanations, and exact citations | **VERIFIED** |
| **Flashcard Deck Generator** | Active recall study materials | Generates front/back cards with difficulty ratings and interactive 3D card flip interface | **VERIFIED** |
| **Multi-Style Summaries** | Pedagogical summaries | 5 summary formats: Executive Brief, Detailed Notes, Key Takeaways, Beginner Analogy, and Exam Cram | **VERIFIED** |
| **Spoken Audio Lessons** | Text-to-speech audio lessons | Browser-native Web Speech API (`speechSynthesis`) with voice selection, pitch, rate control, and audio playback | **VERIFIED** |
| **Progress Tracking & SQLite** | Persistent study logs | SQLite schema tracking `documents`, `quizzes`, `quiz_attempts`, `flashcard_decks`, and `summaries` | **VERIFIED** |
| **Study Dashboard & Analytics** | KPI cards and charts | Recharts visualization of topic mastery, score trends over time, and difficulty distribution | **VERIFIED** |
| **Export Functionality** | Downloadable study materials | Markdown export endpoints (`/api/quiz/{id}/export` and `/api/summary/{id}/export`) for offline study | **VERIFIED** |
| **Error Handling & Boundaries** | Clear user error alerts | Graceful HTTPException (400/404/500), schema validation, and React alert banners | **VERIFIED** |
| **Document Isolation** | Zero cross-document leakage | Multi-document regression tests confirm 0% concept contamination between unrelated uploads | **VERIFIED** |

---

## 6. Capabl 8-Week Submission Deliverables Checklist

- [x] **Week 1:** Project Overview, Problem Statement, Target Users, Success Metrics, Team Roles, 8-Week Plan.
- [x] **Week 2:** Model Selection & Comparison Matrix (Gemini 2.5 Flash vs. GPT-4o-mini vs. Claude 3.5 Haiku), RAG Architecture documentation.
- [x] **Week 3:** Educational Tools Integration (LangChain structured tools, DocumentAgent, QuizAgent, FlashcardAgent, SummaryAgent).
- [x] **Week 4:** Agent Workflow Diagram, System Architecture Mermaid Diagrams, Error Handling & Telemetry.
- [x] **Week 5:** Interactive React Student Frontend (Dashboard, Documents, Chat, Quiz, Flashcards, Summaries, Audio, Analytics).
- [x] **Week 6:** FastAPI Endpoints, CORS configuration, API Documentation (`/docs` & `/redoc`), Frontend-Backend integration.
- [x] **Week 7:** Comprehensive Automated Test Suite (30 unit & regression tests passing), Input validation, Model fallback resilience.
- [x] **Week 8:** Production Cloud Deployments (Vercel & Render), Final Documentation, Video Recording Script, Presentation Deck.
