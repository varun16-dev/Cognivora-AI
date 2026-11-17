# Educational Content Generator AI (EduGen AI)

[![Track](https://img.shields.io/badge/Track-Advanced%20Track%20(Track%20B)-blueviolet.svg)](https://github.com)
[![Architecture](https://img.shields.io/badge/Architecture-Agentic%20AI%20%7C%20RAG-indigo.svg)](https://github.com)
[![Backend](https://img.shields.io/badge/Backend-FastAPI%20%7C%20Python%203.14-009688.svg)](https://fastapi.tiangolo.com)
[![Frontend](https://img.shields.io/badge/Frontend-Next.js%2014%20%7C%20React%20%7C%20TypeScript-black.svg)](https://nextjs.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

> **EduGen AI** is a portfolio-grade, production-oriented Agentic AI educational platform. It transforms raw academic materials (PDFs, DOCX, lecture notes) into an active, adaptive, multimodal learning ecosystem powered by autonomous tool orchestration, strict RAG grounding, an algorithmic learner skill model, and interactive voice Q&A.

---

## Table of Contents
- [Overview](#overview)
- [Problem Statement](#problem-statement)
- [Proposed Solution](#proposed-solution)
- [Features](#features)
- [System Architecture](#system-architecture)
- [Agent Architecture & Tool Selection](#agent-architecture--tool-selection)
- [RAG Pipeline](#rag-pipeline)
- [Educational Tools](#educational-tools)
- [Adaptive Learning Engine](#adaptive-learning-engine)
- [Analytics & Student Dashboard](#analytics--student-dashboard)
- [Voice Q&A](#voice-qa)
- [User Learning Journey](#user-learning-journey)
- [Technology Stack](#technology-stack)
- [Database Architecture](#database-architecture)
- [API Architecture & Documentation](#api-architecture--documentation)
- [Deployment Architecture](#deployment-architecture)
- [Installation](#installation)
- [Environment Variables](#environment-variables)
- [Running Locally](#running-locally)
- [Testing](#testing)
- [Deployment](#deployment)
- [Screenshots & Visual Design Concept](#screenshots--visual-design-concept)
- [Demo Experience Flow](#demo-experience-flow)
- [Team Members](#team-members)
- [Individual Contributions](#individual-contributions)
- [8-Week Roadmap](#8-week-roadmap)
- [Known Limitations](#known-limitations)
- [Future Scope](#future-scope)

---

## Overview

Modern academic study materials—such as university syllabi, dense engineering textbooks, slide decks, and exam revision packets—remain overwhelmingly static. Students typically consume them passively, guessing which concepts they understand until an exam exposes their weaknesses.

**EduGen AI** replaces static reading with an active, closed-loop educational workflow:
$$\mathbf{UPLOAD} \longrightarrow \mathbf{UNDERSTAND} \longrightarrow \mathbf{LEARN} \longrightarrow \mathbf{PRACTICE} \longrightarrow \mathbf{ANALYZE} \longrightarrow \mathbf{ADAPT}$$

By treating uploaded curriculum documents as the single source of truth, EduGen AI orchestrates specialized tools to parse concept hierarchies, ground student question-answering with exact page citations, generate calibrated multi-format quizzes, create spaced-repetition flashcards, produce spoken audio overviews, and continuously recalculate topic-level mastery.

---

## Problem Statement

1. **Information Overload & Passive Fatigue:** Students are expected to comprehend hundreds of pages of technical literature each semester without systematic active recall.
2. **Generative AI Hallucinations:** Standard commercial chat assistants often fabricate facts or introduce external concepts not covered in a specific course syllabus or university exam guide.
3. **Static, Non-Diagnostic Quizzing:** Typical automated quiz generators produce one-off static question lists with zero tracking of past mistakes or topic-level skill deficits.
4. **Fragmented Learning Toolchains:** Learners are forced to alternate across disconnected tools (PDF viewers, flashcard software, TTS readers, and chat interfaces) with no unified analytics engine.

---

## Proposed Solution

EduGen AI addresses these challenges with a cohesive full-stack agentic architecture:
- **Autonomous Agentic Router:** Decouples user intent from hardcoded scripts, routing requests intelligently to specialized tools.
- **Strict RAG Pipeline:** Employs semantic chunking, metadata pre-filtering, and similarity thresholds to eliminate hallucinations and attribute answers to specific document pages.
- **Dynamic Learner Model:** Uses an Exponentially Weighted Moving Average (EWMA) to adjust question difficulty and topic distributions based on actual student performance.
- **Voice-Enabled Multimodal Interaction:** Allows students to listen to synthesized audio summaries and engage in spoken Q&A with automatic text fallback.

---

## Features

- 📄 **Multi-Format Document Parsing:** Ingests PDF, DOCX, and TXT files, extracting hierarchical chapter and topic trees.
- 🎯 **Strictly Grounded Study Assistant:** Multi-turn conversational interface with pedagogical modes ("Explain Simply", "Exam Cram", "Deep Dive") and clickable page citations.
- 📝 **Multi-Difficulty Quiz Generation:** Instant generation of calibrated Multiple Choice Questions (MCQs), True/False, and Fill-in-the-Blank questions with comprehensive pedagogical rationales.
- 🃏 **Interactive Flashcards:** Spaced-repetition study cards with 3D flip animation, self-assessed confidence ratings, and review queue tracking.
- 🎙️ **Audio Learning Lab & Voice Q&A:** Spoken conceptual overviews with variable playback speed ($0.75\times - 2.0\times$) and browser-based voice inquiry.
- 📈 **Mastery Analytics Dashboard:** Topic mastery heatmaps, radar skill distribution, historical score trends, study streak tracking, and personalized revision recommendations.

---

## System Architecture

EduGen AI is engineered with a clean separation of concerns across its presentation, API gateway, orchestration, and persistence layers.

```mermaid
flowchart TD
    subgraph Client ["Frontend Layer (Next.js 14 + Tailwind CSS)"]
        UI["Student Dashboard & Chat Interface"]
        VoiceIO["Voice Recording & Audio Player"]
        AnalyticsViz["Mastery Heatmap & Charts"]
    end

    subgraph Gateway ["API & Security Gateway (FastAPI)"]
        Auth["JWT Authentication & RBAC"]
        RateLimit["Rate Limiter & Input Validator"]
        Router["API Route Controllers"]
    end

    subgraph AgenticCore ["AI Orchestration Layer"]
        Orchestrator["Agent / Tool Router"]
        ToolRegistry["Tool Registry & Execution Engine"]
        Guardrails["Output Validator & Schema Enforcer"]
    end

    subgraph Tools ["Specialized Educational Tools"]
        T1["Content Understanding Tool"]
        T2["RAG Retrieval Tool"]
        T3["Quiz Generation Tool"]
        T4["Flashcard Generation Tool"]
        T5["Smart Summary Tool"]
        T6["Audio / TTS Tool"]
        T7["Adaptive Engine Tool"]
        T8["Analytics Tool"]
    end

    subgraph Storage ["Data & Model Storage"]
        VectorDB[("Vector DB (ChromaDB / pgvector)")]
        Postgres[("Relational DB (PostgreSQL)")]
        FileStore[("Document Storage (Local / S3)")]
    end

    subgraph Models ["LLM & Embedding Foundation"]
        LLM["Foundation LLMs (Gemini / OpenAI / Groq)"]
        Embedder["Embedding Models (text-embedding-004)"]
        AudioModels["STT / TTS Engines (Whisper / Edge-TTS)"]
    end

    UI -->|HTTPS / WSS| Gateway
    VoiceIO -->|Audio Streams| Gateway
    Gateway --> AgenticCore
    Orchestrator --> ToolRegistry
    ToolRegistry --> Tools
    Tools --> Models
    Tools --> Storage
    Guardrails -->|Validated JSON| Gateway
    Gateway --> UI
```

---

## Agent Architecture & Tool Selection

EduGen AI avoids hardcoded single-prompt chains. It employs an autonomous **Orchestrator Agent** that parses natural language requests, reasons over available capabilities in the **Tool Registry**, executes targeted operations, and validates outputs against strict Pydantic schemas.

```mermaid
flowchart TD
    UserQuery(["Student Request: 'Create 5 medium questions on Deadlocks from Chapter 3'"]) --> AgentRouter["Agent / Intent Router"]
    
    AgentRouter --> Decision{"Intent Analysis"}
    
    Decision -->|Conceptual Q&A| T_RAG["RAG Retrieval Tool"]
    Decision -->|Quiz Request| T_Quiz["Quiz Generation Tool"]
    Decision -->|Flashcards| T_Card["Flashcard Tool"]
    Decision -->|Summary / Audio| T_Audio["Summary & TTS Tool"]
    Decision -->|Skill Diagnosis| T_Adapt["Adaptive Engine Tool"]
    
    T_Quiz --> FetchContext["Retrieve Grounded Chunks (RAG)"]
    FetchContext --> LLMCall["Execute LLM with Pydantic QuizSchema"]
    LLMCall --> ValidateOutput{"Output Validator"}
    
    ValidateOutput -->|Schema Valid| SuccessPayload["Format Response with Topic & Citations"]
    ValidateOutput -->|Schema Invalid| RetryLoop["Self-Correction Retry (Feed validation error back)"]
    RetryLoop --> LLMCall
    
    SuccessPayload --> UserDisplay(["Deliver Interactive Quiz to UI"])
```

---

## RAG Pipeline

The RAG engine is built to enforce academic rigor and eliminate generative hallucinations. Every indexed chunk carries rich relational metadata.

```mermaid
flowchart TD
    subgraph Ingestion ["1. Document Ingestion Pipeline"]
        Doc["Raw Document (PDF, DOCX, TXT)"] --> Validation["File Validation & Sanitization"]
        Validation --> Extraction["Text & Layout Extraction (PyMuPDF / pdfplumber)"]
        Extraction --> Cleaner["Text Cleaning & Normalization"]
        Cleaner --> Metadata["Metadata Extraction (Subject, Chapter, Topic)"]
        Metadata --> Chunking["Semantic Chunking (512-800 tokens, 15% overlap)"]
    end

    subgraph EmbeddingStorage ["2. Vectorization & Indexing"]
        Chunking --> Embedder["Embedding Generation (text-embedding-004)"]
        Embedder --> VectorDB[("Vector DB (ChromaDB / pgvector)")]
        Metadata -.->|Document Hierarchy| RelationalDB[("PostgreSQL Metadata")]
    end

    subgraph Retrieval ["3. Retrieval & Synthesis"]
        Query["Student Query / Agent Request"] --> QueryEmbed["Query Vectorization"]
        QueryEmbed --> Filter["Metadata Pre-Filtering (doc_id, chapter)"]
        Filter --> DenseSearch["Dense Vector Similarity (Cosine)"]
        DenseSearch --> Rerank["Cross-Encoder Re-Ranking / Top-K Selection"]
        Rerank --> GroundedContext["Grounded Context Chunks + Citations"]
        GroundedContext --> PromptAssembly["Prompt Assembly with Anti-Hallucination Guard"]
        PromptAssembly --> Generator["LLM Generation"]
        Generator --> Output["Verified, Grounded Response with Page Citations"]
    end
```

### Chunk Metadata Structure
```json
{
  "chunk_id": "doc_9a1e3b_c002_p014_003",
  "document_id": "doc_9a1e3b",
  "filename": "Database_Systems_Concepts.pdf",
  "subject": "Computer Science",
  "chapter": "Chapter 2: Relational Model",
  "topic": "Relational Algebra & Normalization",
  "page_number": 14,
  "chunk_index": 3,
  "created_at": "2026-11-17T18:30:00Z"
}
```

---

## Educational Tools

| Tool Name | Input Parameters | Output Artifact | Key Capabilities |
| :--- | :--- | :--- | :--- |
| **Quiz Generator** | `document_id`, `topic`, `difficulty`, `question_count`, `types` | `Quiz` object with validated questions | MCQs, True/False, Fill-in-Blank; includes answer rationales and source page citations. |
| **Flashcard Generator** | `document_id`, `topic`, `card_count` | Array of `Flashcard` objects | Two-sided cards (Prompt vs. Answer/Rationale), Leitner box status, confidence ratings. |
| **Smart Summary Generator** | `document_id`, `chapter`, `mode` (`quick` \| `detailed` \| `exam_cram`) | Structured Markdown Summary | Extracts core definitions, critical theorems, key takeaways, and revision checklists. |
| **Audio Learning Tool** | `summary_text`, `voice_profile` | Audio stream (`.mp3`) + Timed Cues | High-clarity synthesized speech with synchronized transcript markers. |
| **Adaptive Difficulty Tool** | `user_id`, `topic_id` | Target difficulty (`easy` \| `medium` \| `hard`) | Calibrates next assessment difficulty based on historical accuracy and latency. |
| **Study Recommendation Tool** | `user_id` | Prioritized study action plan | Identifies weak topics ($<60\%$ mastery) and prescribes targeted review intervals. |

---

## Adaptive Learning Engine

Rather than assigning static difficulty tags, EduGen AI models student understanding at the individual topic and subtopic level.

```mermaid
flowchart TD
    Start(["Student Submits Quiz"]) --> Eval["Evaluate Item Responses"]
    Eval --> MetricCalc["Calculate Question Latency, Accuracy, Repeated Errors"]
    MetricCalc --> TopicUpdate["Update Topic Mastery Score: M_t(k)"]
    
    subgraph UpdateLogic ["Mastery Update Function"]
        TopicUpdate --> Formula["M_t(k) = α · Score + (1-α) · M_t(k-1) - Penalty(RepeatedMistakes)"]
    end

    Formula --> Threshold{"Mastery Level Check"}
    Threshold -->|Score < 60%| WeakNode["Flag as WEAK TOPIC (Priority 1)"]
    Threshold -->|60% <= Score < 80%| ModNode["Flag as DEVELOPING (Priority 2)"]
    Threshold -->|Score >= 80%| MasteredNode["Flag as MASTERED (Priority 3)"]

    WeakNode --> NextGen["Next Quiz Generation Rules:"]
    ModNode --> NextGen
    MasteredNode --> NextGen

    NextGen --> Rules["1. Allocate 60% questions to Weak Topics<br/>2. Step down difficulty by one tier (Hard -> Med -> Easy)<br/>3. Inject explanatory concept bridges<br/>4. Schedule spaced re-test in 48 hours"]
    Rules --> End(["Generate Personalized Adaptive Quiz"])
```

---

## Analytics & Student Dashboard

The analytics engine turns raw quiz logs into actionable educational visualizations:
1. **Overall Mastery Metric:** Aggregated weighted readiness score across the entire syllabus.
2. **Topic Mastery Heatmap:** Color-coded matrix showing concept readiness (Green $\ge 80\%$, Amber $60-79\%$, Red $<60\%$).
3. **Weak-Topic Radar:** Multi-axial comparison across chapters highlighting knowledge deficits.
4. **Historical Score Trajectory:** Rolling accuracy trends over time.
5. **Study Streak & Activity Timeline:** Encourages continuous daily study habits.

---

## Voice Q&A

EduGen AI supports a complete multimodal voice loop designed specifically for auditory learners:

```mermaid
flowchart LR
    Mic["Student Speaks Query"] --> STT["Speech-to-Text (Whisper)"]
    STT --> Orchestrator["AI Agent Orchestrator"]
    Orchestrator --> RAG["Grounded RAG Retrieval"]
    RAG --> AnswerGen["Answer Generation + Citations"]
    AnswerGen --> DualOutput{"Response Output"}
    DualOutput --> TextStream["Streaming Text Response to UI"]
    DualOutput --> TTS["Text-to-Speech Engine (Edge-TTS)"]
    TTS --> AudioPlayer["Synchronized Audio Player in UI"]
```

*Note: Voice input is an optional multimodal enhancement; full keyboard and text interaction is always available.*

---

## User Learning Journey

```mermaid
flowchart TD
    U1["1. Student Registers & Logs In"] --> U2["2. Uploads Syllabus / Notes (PDF/DOCX)"]
    U2 --> U3["3. AI Extracts Chapter & Topic Tree"]
    U3 --> U4["4. Student Explores Grounded Assistant Q&A"]
    U4 --> U5["5. Student Requests Diagnostic Quiz"]
    U5 --> U6["6. Instant Pedagogical Review & Grading"]
    U6 --> U7["7. Adaptive Engine Detects Weak Concepts"]
    U7 --> U8["8. Personalized Study Plan & Spaced Flashcards"]
    U8 --> U9["9. Spoken Audio Overview for Auditory Review"]
    U9 --> U10["10. Mastery Heatmap Shows Verified Progress"]
```

---

## Technology Stack

| Layer | Technologies Selected | Justification |
| :--- | :--- | :--- |
| **Frontend** | **Next.js 14 (App Router), React, TypeScript, Tailwind CSS** | Server-side rendering, robust type-safety, rapid UI composition, production scalability. |
| **Backend API** | **FastAPI (Python 3.14 / 3.11+), Pydantic v2, Uvicorn** | High-performance asynchronous IO, native OpenAPI generation, strict data validation. |
| **AI Orchestration** | **Custom Tool-Calling Agent / LangChain Core** | Clean separation of tools, deterministic routing, explicit telemetry, and zero black-box lock-in. |
| **LLMs** | **Google Gemini 1.5 Pro / Flash, OpenAI GPT-4o-mini, Groq Llama-3.3** | High context windows ($>1\text{M}$ tokens for textbooks), low cost per million tokens, fast JSON mode. |
| **Embedding Model** | **Google `text-embedding-004` / OpenAI `text-embedding-3-small`** | Superior MTEB benchmark performance, 768/1536 dimensions, cost-effective vectorization. |
| **Vector Storage** | **ChromaDB (Local MVP) $\rightarrow$ PostgreSQL `pgvector` (Production)** | Fast local prototyping transitioning directly into enterprise relational-vector hybrid storage. |
| **Relational Database**| **PostgreSQL 16, SQLAlchemy 2.0 (Async), Alembic** | ACID transactional safety for user profiles, quiz attempts, and learning telemetry. |
| **Voice / Multimodal**| **Edge-TTS (Synthesis) + Whisper Local / Web Speech API (Recognition)**| High-fidelity natural speech synthesis without prohibitive per-character API costs. |

---

## Database Architecture

EduGen AI pairs an ACID-compliant relational schema in PostgreSQL with a vector store for semantic embeddings.

```mermaid
erDiagram
    USERS ||--o{ DOCUMENTS : uploads
    USERS ||--o{ STUDY_SESSIONS : conducts
    USERS ||--o{ QUIZ_ATTEMPTS : submits
    USERS ||--o{ FLASHCARD_REVIEWS : performs
    USERS ||--o{ LEARNER_METRICS : possesses

    DOCUMENTS ||--o{ DOCUMENT_CHUNKS : contains
    DOCUMENTS ||--o{ TOPICS : identifies
    
    TOPICS ||--o{ QUESTIONS : categorizes
    TOPICS ||--o{ FLASHCARDS : classifies
    TOPICS ||--o{ LEARNER_METRICS : tracks

    QUIZZES ||--o{ QUESTIONS : contains
    QUIZZES ||--o{ QUIZ_ATTEMPTS : records
    QUIZ_ATTEMPTS ||--o{ QUESTION_RESPONSES : includes

    USERS {
        uuid id PK
        string email UK
        string hashed_password
        string full_name
        string role
        timestamp created_at
    }

    DOCUMENTS {
        uuid id PK
        uuid user_id FK
        string filename
        string file_path
        integer file_size
        string mime_type
        string detected_subject
        string processing_status
        timestamp uploaded_at
    }

    DOCUMENT_CHUNKS {
        uuid id PK
        uuid document_id FK
        integer chunk_index
        text content
        integer page_number
        string chapter
        string topic
        string vector_id
    }

    TOPICS {
        uuid id PK
        uuid document_id FK
        string name
        string chapter
        string difficulty_baseline
    }

    QUIZZES {
        uuid id PK
        uuid user_id FK
        uuid document_id FK
        string title
        string difficulty_target
        boolean is_adaptive
        timestamp created_at
    }

    QUESTIONS {
        uuid id PK
        uuid quiz_id FK
        uuid topic_id FK
        string question_type
        text prompt
        jsonb options
        string correct_answer
        text explanation
        string difficulty
        jsonb source_reference
    }

    QUIZ_ATTEMPTS {
        uuid id PK
        uuid quiz_id FK
        uuid user_id FK
        float score_percentage
        integer total_time_seconds
        timestamp completed_at
    }

    LEARNER_METRICS {
        uuid id PK
        uuid user_id FK
        uuid topic_id FK
        float mastery_score
        integer total_attempts
        integer correct_attempts
        timestamp last_reviewed_at
    }
```

---

## API Architecture & Documentation

All backend routes adhere to RESTful best practices and return structured, type-checked JSON.

```mermaid
flowchart LR
    Client["Next.js Client"] -->|Authorization: Bearer JWT| AuthDep["FastAPI Dependency Injection"]
    AuthDep -->|Validated User| Endpoints{"API Endpoints"}

    Endpoints --> AuthRoutes["/api/v1/auth<br/>(register, login)"]
    Endpoints --> DocRoutes["/api/v1/documents<br/>(upload, hierarchy)"]
    Endpoints --> AgentRoutes["/api/v1/agent<br/>(chat, citations)"]
    Endpoints --> QuizRoutes["/api/v1/quiz<br/>(generate, submit)"]
    Endpoints --> CardRoutes["/api/v1/flashcards<br/>(generate, review)"]
    Endpoints --> AudioRoutes["/api/v1/audio<br/>(generate, stream)"]
    Endpoints --> AnalyticsRoutes["/api/v1/analytics<br/>(mastery, heatmaps)"]
```

### Core Endpoint Summary
- `POST /api/v1/auth/register` — Create user account
- `POST /api/v1/auth/login` — Authenticate and receive JWT token
- `POST /api/v1/documents/upload` — Upload and trigger asynchronous chunking
- `GET  /api/v1/documents/{id}/hierarchy` — Retrieve syllabus structure
- `POST /api/v1/agent/chat` — Contextual study chat with citations
- `POST /api/v1/quiz/generate` — Generate standard or adaptive quiz
- `POST /api/v1/quiz/submit` — Submit answers and update mastery metrics
- `POST /api/v1/flashcards/generate` — Generate study deck
- `POST /api/v1/audio/generate` — Generate synthesized spoken lesson
- `GET  /api/v1/analytics/dashboard` — Fetch student mastery metrics and weak topics

---

## Deployment Architecture

```mermaid
flowchart TD
    subgraph Users ["Client Devices"]
        Browser["Desktop & Mobile Browsers"]
    end

    subgraph CDN ["Edge & CDN"]
        VercelEdge["Vercel Edge Network (Next.js 14)"]
    end

    subgraph CloudApp ["Backend Cloud Container (Render / AWS ECS)"]
        DockerFastAPI["FastAPI Docker Container (Uvicorn Workers)"]
        WorkerQueue["Background Task Processing (Ingestion)"]
    end

    subgraph CloudStorage ["Persistence Layer"]
        ManagedPG[("Managed PostgreSQL (Supabase / RDS)")]
        ManagedVector[("ChromaDB Persistent Volume / pgvector")]
        ObjectStore[("S3 / Cloud Storage (PDFs & Audio)")]
    end

    Browser -->|HTTPS| VercelEdge
    VercelEdge -->|REST / SSE| DockerFastAPI
    DockerFastAPI --> ManagedPG
    DockerFastAPI --> ManagedVector
    DockerFastAPI --> WorkerQueue
    WorkerQueue --> ObjectStore
```

---

## Installation

### Prerequisites
- **Python:** 3.11+ (Tested on Python 3.14)
- **Node.js:** v18.0+ (Tested on Node v24.14)
- **Git:** 2.40+

### Clone Repository
```bash
git clone https://github.com/your-org/educational-content-generator-ai.git
cd educational-content-generator-ai
```

---

## Environment Variables

Copy the template configuration file:
```bash
cp .env.example .env
```

Ensure your `.env` contains the required credentials:
```env
ENVIRONMENT=development
SECRET_KEY=your_secret_key_here
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/edugen_ai
OPENAI_API_KEY=your_openai_key
GEMINI_API_KEY=your_gemini_key
GROQ_API_KEY=your_groq_key
```

---

## Running Locally

### 1. Backend Setup
```bash
# Navigate to backend and create virtual environment
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Start FastAPI development server
uvicorn app.main:app --reload --port 8000
```
Backend API will be accessible at: `http://localhost:8000` (Swagger UI at `/docs`).

### 2. Frontend Setup
```bash
# Navigate to frontend in a new terminal
cd frontend

# Install npm dependencies
npm install

# Start development server
npm run dev
```
Frontend web application will be accessible at: `http://localhost:3000`.

---

## Testing

EduGen AI includes comprehensive automated testing across unit, integration, and RAG evaluation tiers:

```bash
# Run backend unit and integration test suite
cd backend
pytest -v --tb=short

# Run workspace and architecture verification
python tests/test_workspace_sanity.py
```

---

## Deployment

- **Frontend:** Automatically built and hosted on **Vercel** with custom domain routing.
- **Backend API:** Packaged via Dockerfile:
  ```dockerfile
  FROM python:3.11-slim
  WORKDIR /app
  COPY requirements.txt .
  RUN pip install --no-cache-dir -r requirements.txt
  COPY . .
  CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
  ```

---

## Screenshots & Visual Design Concept

> *Note: UI implementation commences in Week 5 according to the 8-week delivery plan. Below is the approved design layout.*

```
+-----------------------------------------------------------------------------------+
|  EduGen AI                [Search Topics...]            (Streak: 🔥 5) [Profile]  |
+-----------------------------------------------------------------------------------+
|  DASHBOARD                                                                        |
|  Overall Mastery: [████████████░░░░] 74%       Study Time: 14.2 hrs               |
|                                                                                   |
|  TOPIC MASTERY HEATMAP:                                                           |
|  [■ Process Scheduling - 92%]   [■ Memory Management - 84%]                       |
|  [▲ Deadlocks - 61%]            [● Graph Traversal - 43% (NEEDS REVIEW)]          |
|                                                                                   |
|  RECOMMENDED ACTION:                                                              |
|  "Reinforce Graph Traversal: Take a 5-question adaptive review quiz."             |
|  [ Start Adaptive Quiz ]     [ Listen to 5-Min Summary ]                          |
+-----------------------------------------------------------------------------------+
```

---

## Demo Experience Flow

The planned live evaluation and viva demonstration follows an uninterrupted user journey:
1. **Authentication:** Log into the personal student workspace.
2. **Document Ingestion:** Upload an academic syllabus (`Operating_Systems_Unit3.pdf`).
3. **Hierarchy Inspection:** View auto-detected chapters, topics, and difficulty baseline.
4. **Contextual Q&A:** Ask a technical question; observe streaming response with page citations.
5. **Diagnostic Quiz:** Take a 5-question initial assessment.
6. **Intentional Mistake Analysis:** Simulate errors on a specific concept (e.g., Banker's Algorithm).
7. **Adaptive Trigger:** Observe the system flag the weak topic and auto-calibrate the subsequent quiz.
8. **Spoken Review:** Play the synthesized 5-minute audio overview with transcript markers.
9. **Analytics Validation:** View the real-time update in the topic mastery heatmap.

---

## Team Members

1. **Varun D** — Lead AI/ML Engineer & Agent Architect
2. **Sindhuja S** — Lead Frontend & UI/UX Engineer
3. **Mohith S** — Lead Backend & Platform Engineer

---

## Individual Contributions

| Team Member | Direct Technical Ownership |
| :--- | :--- |
| **Varun D** | • AI Orchestrator & Tool Selection Engine<br/>• RAG Pipeline, semantic chunking & vector retrieval<br/>• Model benchmarking (`docs/MODEL_COMPARISON.md`)<br/>• Adaptive learning mathematical engine (`docs/ADAPTIVE_LEARNING.md`)<br/>• Anti-hallucination guardrails & structured Pydantic validation |
| **Sindhuja S** | • Next.js 14 App Router, TypeScript & Tailwind CSS architecture<br/>• Visual design system tokens & theme configuration<br/>• Interactive Student Dashboard & Mastery Heatmaps<br/>• Interactive Quiz runner, Flashcard 3D flip card & Audio player UI<br/>• Mobile, tablet, and desktop responsive layout engineering |
| **Mohith S** | • FastAPI backend architecture & dependency injection<br/>• PostgreSQL schema, ORM models, and Alembic migrations<br/>• JWT authentication, secure password hashing & RBAC<br/>• API controllers & OpenAPI documentation (`docs/API.md`)<br/>• Docker containerization, CI/CD pipeline & cloud deployment |

---

## 8-Week Roadmap

- [x] **Week 1: Foundations & Architecture** — Project specifications, Master Project Plan (`docs/PROJECT_PLAN.md`), README with Mermaid architecture, team responsibility matrix, and repository initialization.
- [ ] **Week 2: Model Evaluation & Core RAG Pipeline** — LLM & embedding model benchmarking, document parsers, semantic chunker, and vector indexing.
- [ ] **Week 3: Tool Registry & Agent Routing** — Quiz, Flashcard, and Summary generation tools with autonomous agent routing.
- [ ] **Week 4: End-to-End Agent & Voice Q&A** — Multi-turn conversation agent, Speech-to-Text, and Text-to-Speech audio integration.
- [ ] **Week 5: Next.js Frontend Foundation** — Component library, Student Dashboard, Document Explorer, and Chat UI.
- [ ] **Week 6: Full Backend APIs & Database Persistence** — PostgreSQL persistence, JWT auth, quiz submission endpoints, and API docs.
- [ ] **Week 7: Adaptive Engine, Testing & Guardrails** — Dynamic skill modeling, edge-case testing, and latency optimization.
- [ ] **Week 8: Production Deployment & Demo** — Cloud deployment, live URL, video demonstration, and final project defense.

---

## Known Limitations

- **Scanned Image PDFs:** Documents lacking native digital text layers require external OCR preprocessing before ingestion.
- **Formula & Diagram Parsing:** Complex mathematical formulas and circuit diagrams are currently ingested as text descriptions rather than native LaTeX/CAD representations (planned for future scope).
- **Audio Synthesis Languages:** TTS is currently calibrated and optimized for standard English technical terminology.

---

## Future Scope

- **Multi-User Study Lounges:** Collaborative real-time quiz challenges and synchronized flashcard review sessions.
- **Multimodal Visual Reasoning:** Direct question-answering over textbook diagrams, charts, and architectural schematics.
- **Native Mobile Apps:** Offline-first iOS and Android companion applications for flashcard spaced repetition.
- **LMS Interoperability (LTI):** Direct synchronization with Canvas, Moodle, and Google Classroom.
