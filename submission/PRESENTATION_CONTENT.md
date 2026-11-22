# Cognivora AI — Final Presentation Slide Content (10 Slides)

### Slide 1: Title & Project Identity
- **Title:** Cognivora AI — Educational Content Generator AI Agent
- **Subtitle:** Autonomous Multi-Agent Pedagogical Assistant Grounded in Syllabus Courseware
- **Track:** Capabl Agentic AI Hackathon — Track A (Essential) Enhanced with React
- **Team Members:**
  - Varun D (Team Lead & AI Integration)
  - Sindhuja S (Frontend & UI/UX Engineering)
  - Mohith S (Backend & Database Engineering)
- **Live URLs:**
  - Frontend: `https://cognivora-ai.vercel.app`
  - Backend: `https://cognivora-backend.onrender.com`
  - GitHub: `https://github.com/varun16-dev/Cognivora-AI`

---

### Slide 2: The Problem & Academic Bottlenecks
- **Passive Learning Inefficacy:** Students retain less than 30% of technical textbook content after 48 hours without active recall.
- **AI Hallucinations & Distractions:** Public LLMs generate generic or incorrect information outside syllabus scope, confusing students before exams.
- **Fragmented Study Toolchains:** Learners juggle separate PDF viewers, quiz generators, flashcard apps, and text-to-speech tools without unified progress tracking.
- **Lack of Diagnostic Assessment:** Standard quiz tools provide no difficulty calibration or cognitive analysis of weak areas.

---

### Slide 3: Project Objectives & Track A Scope
- **Core Mission:** Provide a self-contained, syllabus-grounded educational ecosystem where students upload courseware and receive verified active learning resources.
- **Track A Alignment:**
  - Ingestion of PDF, DOCX, and TXT files.
  - Document-grounded RAG with strict isolation.
  - Contextual AI study chat with source citations.
  - Calibrated assessment engine (Easy, Medium, Hard).
  - Active recall flashcards and multi-mode summaries.
  - Zero-credit browser audio lessons via Web Speech API.
  - Topic mastery tracking and analytics using SQLite.

---

### Slide 4: Multi-Agent System Architecture
- **Coordinator Agent:** Semantic intent classification, educational mode routing, and response synthesis.
- **Document Agent:** Hierarchical topic extraction, text chunking (500 tokens / 100 overlap), and ChromaDB indexing.
- **Quiz Agent:** Bloom's taxonomy difficulty enforcement, over-sampling candidate validation, and duplicate prevention.
- **Flashcard & Summary Agents:** Active recall generation with 5 pedagogical summary styles.
- **Adaptive Learning Engine:** Real-time student skill modeling using Exponentially Weighted Moving Averages (EWMA).

---

### Slide 5: RAG Pipeline & Anti-Hallucination Boundaries
- **Strict Document ID Filtering:** Every ChromaDB query enforces `where={"document_id": target_id}`.
- **Zero Cross-Document Leakage:** Chunks from other documents are physically filtered at retrieval and prompt construction layers.
- **Verifiable Citations:** Responses cite exact document page numbers and chunk similarity metrics.
- **Fallback Cosine Search:** Fast in-memory embedding search ensures continuous operation even when vector servers are cold.

---

### Slide 6: Calibrated Quiz Engine & Difficulty Enforcement
- **Easy Tier:** Definitions, core terminology, basic factual identification, and clear True/False.
- **Medium Tier:** $\ge 70\%$ applied reasoning, formula calculations ($E_n(x)$), and technique comparisons. Rejects bare dictionary definitions.
- **Hard Tier:** $\ge 80\%$ multi-step scenarios (e.g. cryptanalysis attack scenarios); strictly forbids True/False and one-step arithmetic.
- **Anti-Repetition:** Jaccard token similarity ($\ge 0.55$) prevents repeated questions across consecutive quizzes on the same topic.

---

### Slide 7: Frontend Engineering & Student Experience
- **Modern Stack:** React 19, Vite, Tailwind CSS, Lucide icons, and Recharts.
- **Mathematical Typography:** Integrated `remark-math` and `rehype-katex` for crisp LaTeX equation rendering ($E(p) = (p + k) \bmod 26$).
- **Responsive Station Layout:** Clean navigation between Document Management, AI Study Chat, Quiz Station, Flashcard Decks, Audio Lab, and Analytics.
- **Web Speech Audio:** Native browser audio synthesis with speed, pitch, and voice controls.

---

### Slide 8: Comprehensive Verification & Test Results
- **30 / 30 Automated Tests Passed (100% Success Rate):**
  - 8 Quiz Difficulty, Diversity & Anti-Repetition tests.
  - 5 Strict Document Isolation regression tests.
  - 12 FastAPI REST endpoint and schema tests.
  - 5 Workspace sanity and database tests.
- **Frontend Production Build:** Vite build bundles cleanly in 1.43s with 0 errors.

---

### Slide 9: Impact, Evaluation & Student Mastery
- **Immediate Retention Boost:** Active recall through calibrated quizzes and 3D flashcards strengthens long-term memory.
- **Targeted Revision:** Knowledge deficit alerts automatically highlight topics with mastery $<60\%$.
- **Transparent Decision Telemetry:** Students and evaluators can inspect which tools and source chunks were used for every AI response.

---

### Slide 10: Future Scope & Roadmap
- **Track B Transition:** Automated lecture slide PowerPoint generation (`.pptx`) and multi-student collaborative study rooms.
- **Offline Edge Deployment:** Integration with local quantized LLMs (such as Gemma 2B via WebLLM) for fully disconnected mobile study.
- **Canvas / Moodle LMS Integration:** LTI 1.3 compliance for seamless university syllabus syncing.
