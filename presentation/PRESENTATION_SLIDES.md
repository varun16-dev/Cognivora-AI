# Cognivora AI — Final Presentation Slide Deck

**Program:** Capabl Agentic AI Project  
**Selected Track:** Track A (Essential) with React.js SaaS Dashboard Enhancement  
**Project Title:** Cognivora AI — Educational Content Generator AI Agent  
**Team Members:** Varun D (Lead & AI Integration), Sindhuja S (Frontend & UI/UX), Mohith S (Backend & Database)  
**PowerPoint File:** `presentation/Cognivora_AI_Final_Presentation.pptx`

---

## Slide 1: Title & Overview
* **Header:** COGNIVORA AI — CAPABL AGENTIC AI
* **Title:** Autonomous Educational Content Generator AI Agent
* **Subtitle:** An Agentic AI Study Companion Transforming Static Curricula into Active, Adaptive Mastery
* **Team:**
  * **Varun D** — Team Lead & AI Integration (Coordinator Agent, RAG Pipeline, Gemini 2.5 Flash)
  * **Sindhuja S** — Lead Frontend & UI/UX (React 19, Tailwind CSS, Recharts Dashboard)
  * **Mohith S** — Lead Backend & Database (FastAPI, SQLite, Document Processing)

---

## Slide 2: Problem Statement
* **1. Passive Reading Fatigue:** Students spend up to 40% of study time highlighting 50-to-100-page textbooks without active recall, leading to rapid forgetting.
* **2. Generic AI Hallucinations:** General-purpose LLMs fabricate citations, invent formulas, and drift beyond syllabus boundaries.
* **3. Static, Non-Adaptive Assessments:** Question banks don't adapt to student weaknesses or track historical failure patterns.
* **4. Fragmented Tool Sprawl:** Students juggle PDF readers, Anki flashcard apps, audio players, and spreadsheets with zero unified intelligence.

---

## Slide 3: Proposed Solution — Cognivora AI
* **Autonomous Multi-Agent Architecture:** Specialized agents (Document, Quiz, Flashcard, Summary) orchestrated by an intelligent Coordinator Agent via LangChain tools.
* **Context-Grounded RAG Pipeline:** Semantic vector search (ChromaDB) with strict page-level citations and anti-hallucination guardrails.
* **Closed-Loop Adaptive Skill Modeling:** Exponentially Weighted Moving Average (EWMA) topic mastery diagnostic flagging weak topics (<60%) for targeted intervention.
* **Multimodal Active Learning:** Bloom-calibrated quizzes, 3D flip flashcards, 5 pedagogical summary styles, and browser Web Speech audio lessons.

---

## Slide 4: Project Objectives (Capabl Track A)
* **Objective 1:** Ingest multi-format academic documents (PDF via PyMuPDF, DOCX, TXT) with semantic chunking and outline extraction.
* **Objective 2:** Implement genuine agentic tool dispatch using LangChain `@tool` abstractions and SQLite telemetry.
* **Objective 3:** Generate calibrated MCQs, True/False, Fill-in-Blank questions, Leitner flashcards, and multi-tier summaries.
* **Objective 4:** Persist all quiz results and agent decision logs in SQLite, calculating topic mastery and revision plans.
* **Objective 5:** Deliver a production-grade React 19 + Tailwind CSS SaaS dashboard with Recharts visualizations.

---

## Slide 5: Technology Stack & Architectural Decisions
* **Frontend:** React 19 + Vite + Tailwind CSS + Recharts + Lucide React icons.
* **Backend:** Python 3.14 + FastAPI + Pydantic v2 + Uvicorn.
* **AI & Orchestration:** Google Gemini 2.5 Flash (`google-genai` official SDK) + LangChain Core Tools.
* **Vector Database:** ChromaDB 1.5+ persistent store with FastCurriculumEmbedder.
* **Relational Storage:** SQLite with SQLAlchemy ORM models (`documents`, `quizzes`, `quiz_attempts`, `agent_logs`).
* **Audio Synthesis:** Browser Web Speech API (`SpeechSynthesis`) with playback speed and voice customization.

---

## Slide 6: Multi-Agent System Architecture
* **Coordinator Agent:** Classifies student intent (`qa`, `quiz`, `flashcard`, `summary`, `analytics`), invokes LangChain tools, and logs execution telemetry to SQLite.
* **Document Agent:** Ingests documents, extracts chapter outlines, semantically chunks text (650 chars/120 overlap), and indexes ChromaDB.
* **Quiz Agent:** Produces calibrated MCQs, True/False, and Fill-in-Blank questions across Easy, Medium, and Hard tiers with option verification.
* **Flashcard Agent:** Synthesizes atomic active-recall cards with spaced-repetition ratings.
* **Summary Agent:** Generates 5 distinct educational modes: Short (2-min), Detailed, Key Points, Beginner (ELI5), and Exam Cram.

---

## Slide 7: RAG Pipeline & Grounding Guardrails
* **1. Ingestion:** PyMuPDF and python-docx extract clean text and outline hierarchy.
* **2. Overlapping Chunking:** 650-character windows with 120-character overlap preserve technical definitions.
* **3. Vector Indexing:** Normalized 384-dimensional embeddings indexed in ChromaDB.
* **4. Similarity Search:** Cosine similarity retrieval filtered by document and topic.
* **5. Grounding Guardrail:** If similarity is <0.20 or content is missing, the agent explicitly refuses to answer rather than hallucinating.
* **6. Page Citations:** Responses include verified document name, page number, chunk index, and similarity score.

---

## Slide 8: Core Application Features
* **Student Dashboard:** Real-time KPI metrics, study streak badge, Recharts mastery bar chart, score trajectory line chart, and weak topic alerts.
* **Document Manager:** Drag-and-drop upload for PDF/DOCX/TXT with real-time syllabus outline inspector.
* **AI Study Chat:** Grounded multi-turn conversational tutor with 4 pedagogical personas and Agent Decision Inspector.
* **Quiz Generator & Runner:** Timed practice station with progress bar, automated scoring, answer explanations, and Markdown export.
* **3D Flashcards:** Interactive cards with 3D CSS flip animations and Leitner review intervals.
* **Audio Learning Lab:** Browser Web Speech API reader with Play/Pause/Stop, rate/pitch sliders, and live waveform visualizer.

---

## Slide 9: Testing, Verification & Quality Assurance
* **Backend Pytest Suite:** 11 of 11 tests PASSED in 5.35s (`pytest tests/test_backend_api.py`).
* **Workspace Sanity Checks:** 5 of 5 checks PASSED (`python tests/test_workspace_sanity.py`).
* **Frontend Production Build:** Built in 1.91s with 2,542 modules and 0 compilation errors (`npm run build`).
* **Input Validation:** Rejects 0-byte files and unsupported formats with HTTP 400.
* **Anti-Hallucination:** Refuses out-of-scope questions without emitting fake citations.
* **Resilience:** Graceful Demonstration Mode fallback if API key is missing or quota is exceeded.

---

## Slide 10: Conclusion, Limitations & Future Roadmap
* **Project Delivery:** All 8 weeks of Capabl Track A deliverables complete, fully tested, and documented.
* **Current Limitations:**
  * Live cloud LLM calls require the user to configure `GEMINI_API_KEY` in `.env` (Demonstration Mode active by default).
  * Cloud persistence on Render requires a paid disk mount ($7/mo Starter) — free tier storage is ephemeral.
  * Mathematical formula and diagram extraction currently focuses on digital text layers.
* **Future Roadmap:**
  * LMS integration (SCORM and Canvas/Moodle data export plugins).
  * Multi-lingual regional audio lessons (Hindi, Kannada, Tamil, Telugu).
  * Real-time multiplayer peer study quizzes.
