# Cognivora AI — System & Agent Architecture Specification

## 1. System Architecture Overview

Cognivora AI follows a decoupled, three-tier architecture comprising a modern React single-page application, a high-throughput FastAPI backend server, and an autonomous multi-agent orchestration layer connected to ChromaDB and Google Gemini.

```mermaid
flowchart TD
    subgraph Client ["Frontend Layer (React 19 + Vite + Tailwind CSS)"]
        Dashboard["Student Dashboard & Study KPIs"]
        DocManager["Document Uploader & Syllabus Hierarchy"]
        ChatStation["AI Study Assistant (KaTeX LaTeX Math)"]
        QuizStation["Adaptive Quiz Station & Review"]
        CardStation["3D Spaced-Repetition Flashcards"]
        SummaryStation["Multi-Mode Pedagogical Summaries"]
        AudioStation["Web Speech Audio Lesson Player"]
        AnalyticsStation["Recharts Mastery & Deficit Trends"]
    end

    subgraph Gateway ["Backend Gateway (FastAPI + Uvicorn)"]
        Router["API Router (/api)"]
        CORS["CORS & Request Validation"]
        Telemetry["Agent Decision Telemetry"]
    end

    subgraph Agents ["Autonomous Multi-Agent Orchestration Engine"]
        Coordinator["Coordinator Agent (Intent Dispatcher)"]
        DocAgent["Document Agent (Parser & Vector Indexer)"]
        QuizAgent["Quiz Agent (Difficulty & Assessment Engine)"]
        FlashcardAgent["Flashcard Agent (Active Recall Deck Builder)"]
        SummaryAgent["Summary Agent (Pedagogical Digest Engine)"]
        AdaptiveEngine["Adaptive Engine (EWMA Skill Modeler)"]
    end

    subgraph Storage ["Persistent Data Layer"]
        ChromaStore["ChromaDB Vector Store (/data/chroma)"]
        SQLiteStore["SQLite Database (cognivora.db)"]
    end

    subgraph CloudAI ["Foundation LLM Services"]
        GeminiClient["Google Gemini API (3.1-flash-lite / 3.5-flash-lite)"]
        EmbeddingEngine["FastCurriculumEmbedder / Cosine Space"]
    end

    Client -->|REST API Requests| Gateway
    Gateway --> Agents
    Coordinator --> DocAgent
    Coordinator --> QuizAgent
    Coordinator --> FlashcardAgent
    Coordinator --> SummaryAgent
    Coordinator --> AdaptiveEngine
    DocAgent --> ChromaStore
    DocAgent --> SQLiteStore
    QuizAgent --> ChromaStore
    QuizAgent --> GeminiClient
    FlashcardAgent --> GeminiClient
    SummaryAgent --> GeminiClient
    Agents --> SQLiteStore
```

---

## 2. Autonomous Multi-Agent Roles

| Agent | Core Responsibility | Implemented Logic |
| :--- | :--- | :--- |
| **Coordinator Agent** | Central dispatcher and intent classification | Classifies student inputs into Q&A, quiz requests, summary requests, or skill audits; coordinates tool execution and bundles citations. |
| **Document Agent** | Ingestion, parsing, and vector indexing | Extracts text from PDF, DOCX, and TXT; extracts syllabus topics; generates overlapping semantic chunks; embeds and persists vectors into ChromaDB. |
| **Quiz Agent** | Assessment generation and validation | Queries ChromaDB for topic-specific chunks; checks SQLite history to prevent repetitive questions; enforces Bloom's taxonomy difficulty criteria; validates candidate options, keys, and page citations. |
| **Flashcard Agent** | Active recall deck synthesis | Extracts high-yield terms, formulas, and operational mechanisms; generates front/back cards with difficulty calibration. |
| **Summary Agent** | Pedagogical condensation | Produces 5 distinct summary modes tailored to student cognitive needs: Executive Brief, Detailed Notes, Key Takeaways, Beginner Analogy, and Exam Cram. |
| **Adaptive Learning Engine** | Student skill and mastery modeling | Tracks historical quiz attempts in SQLite; computes Exponentially Weighted Moving Average (EWMA) topic scores; flags topics $<60\%$ as critical deficits. |

---

## 3. RAG (Retrieval-Augmented Generation) Pipeline

```mermaid
flowchart LR
    A["Raw Document (.pdf, .docx, .txt)"] --> B["DocumentParser (PyMuPDF / python-docx)"]
    B --> C["Semantic Chunker (500 tokens, 100 overlap)"]
    C --> D["FastCurriculumEmbedder (Normalized Vectors)"]
    D --> E["ChromaDB Collection (where={'document_id': doc_id})"]
    
    Query["User Query / Topic Selection"] --> F["Vector Similarity Search (top_k=5)"]
    E --> F
    F --> G["Strict Document Isolation Boundary"]
    G --> H["Prompt Construction with Page References"]
    H --> I["Google Gemini Generation (Structured JSON)"]
    I --> J["Verified Output with Citations"]
```

### RAG Boundary & Isolation Guarantees
- **Strict Document ID Partitioning:** Vector queries always pass `where={"document_id": document_id}`.
- **Cross-Contamination Guard:** If semantic search returns fewer than 2 chunks, direct chunk fetching is restricted strictly to chunks belonging to `document_id`. Chunks from any other document are discarded at the retrieval boundary.
- **Verifiable Page Citations:** Every retrieved chunk preserves its original document page index (`Page X, <filename>`), ensuring that all answers and questions reference verifiable source material.

---

## 4. Assessment Generation & Anti-Repetition Pipeline

```mermaid
sequenceDiagram
    autonumber
    actor Student
    participant UI as React Quiz Generator
    participant API as FastAPI /api/quiz/generate
    participant Agent as QuizAgent
    participant DB as SQLite (cognivora.db)
    participant RAG as ChromaDB Vector Store
    participant LLM as Google Gemini API

    Student->>UI: Select Document, Topic, Difficulty & Count
    UI->>API: POST /api/quiz/generate
    API->>Agent: generate_quiz(document_id, topic, difficulty, count)
    Agent->>DB: Query last 10 quizzes for document_id (extract historical questions)
    Agent->>RAG: retrieve_relevant_chunks(topic, document_id)
    RAG-->>Agent: Document-grounded context chunks with page numbers
    Agent->>LLM: Prompt over-sampled candidates (count + 4) with difficulty rules & anti-repetition blacklist
    LLM-->>Agent: Raw candidate JSON array
    Agent->>Agent: Validate schema, options, citations, Bloom's difficulty match
    Agent->>Agent: Deduplicate against history and current batch (Jaccard < 0.55)
    Agent->>DB: Persist validated QuizModel in SQLite
    Agent-->>API: Quiz record
    API-->>UI: Return calibrated QuizResponse
    UI-->>Student: Render interactive assessment with timer
```

---

## 5. Backend/Frontend Integration

- **Frontend-Backend Contract:** Typed Pydantic v2 schemas mirror React state objects (`QuizQuestion`, `QuizResponse`, `DocumentResponse`, `ChatMessageResponse`).
- **Proxy Rewrites:** `frontend/vercel.json` transparently proxies all requests from `/api/*` to `https://cognivora-backend.onrender.com/api/*`, eliminating CORS complexities in production.
- **Client Resilience:** React frontend includes standard retry logic, loading spinners, and dismissible alert banners for clean UX during cold starts or transient API rate limits.
