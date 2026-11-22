# Cognivora AI — 5-Minute Live Demonstration Script

**Track:** Capabl Track A (Essential)  
**Team Members:** Varun D (Team Lead & AI Integration), Sindhuja S (Frontend & UI/UX), Mohith S (Backend & Database)  
**Demo Duration:** 5 Minutes  
**Live Application URL:** [https://cognivora-ai.vercel.app](https://cognivora-ai.vercel.app)

---

### Step 1: Introduction & Mission (0:00 – 0:45)
**Speaker:** Varun D
> *"Good morning, evaluators and mentors. University students face two major hurdles today: passive information fatigue from hundreds of pages of dense technical notes, and ungrounded AI chatbots that invent facts outside their syllabus.*
> 
> *To solve this, our team built **Cognivora AI** — an autonomous multi-agent educational assistant designed for Capabl Track A. Cognivora AI ingests course materials and automatically generates grounded study chats, difficulty-calibrated quizzes, spaced-repetition flashcards, pedagogical summaries, spoken audio lessons, and adaptive mastery analytics."*

---

### Step 2: Document Ingestion & Syllabus Outlines (0:45 – 1:30)
**Action:** Navigate to **"Upload Documents"** (`/documents`).
> *"Let's begin in the Document Management station. We support PDF, DOCX, and TXT files.*
> 
> *Here, we have uploaded `LectureNotes_BAD703_Data Security and Privacy.pdf`. When uploaded, our backend **Document Agent** parsed the file using PyMuPDF, segmented the text into semantic chunks with 100-token overlaps, and generated a persistent vector index in ChromaDB.*
> 
> *Notice when we click **Outline**, our regex and NLP pipeline has auto-extracted syllabus topics: 'Classical Encryption Techniques', 'Caesar Cipher', 'Substitution Ciphers', and 'Frequency Analysis'."*

---

### Step 3: Grounded AI Study Assistant & KaTeX Math (1:30 – 2:30)
**Action:** Navigate to **"AI Study Chat"** (`/chat`).
> *"Next, let's open the AI Study Assistant. We select mode **⚡ Exam Cram** and ask:*
> 
> *'Explain the mathematical formulation of the Caesar cipher and why it is vulnerable to frequency analysis.'*
> 
> *Notice three critical features:*
> 1. *The mathematical formulas render in clean LaTeX equation typography ($E(p) = (p + k) \bmod 26$) thanks to our KaTeX integration.*
> 2. *The response includes verified **Grounded Source Citations** linking to Page 1 of the Data Security document with semantic similarity scores.*
> 3. *If we click **Inspect Agent Decision**, the Coordinator Agent exposes its reasoning telemetry: intent detection, tools invoked, and execution latency."*

---

### Step 4: Calibrated Quiz Generation & Grading (2:30 – 3:30)
**Action:** Navigate to **"Quiz Generator"** (`/quiz`).
> *"Now let's test our assessment engine. We select our document, choose Topic 'Classical Encryption Techniques', and select **HARD** difficulty for 3 questions.*
> 
> *Our upgraded Quiz Agent enforces Bloom's taxonomy: for Hard mode, it strictly disallows trivial True/False guesses or simple definitions. Instead, it generates multi-step analytical scenarios — such as an attacker intercepting ciphertext and deducing the unknown key.*
> 
> *Let's select our answers interactively and click **Submit & Grade Quiz**. Instantly, the backend records the attempt in SQLite and returns our score percentage, correct answer keys, pedagogical explanations, and exact page references.*
> 
> *If we click **Retake**, our current quiz is preserved; clicking **New Quiz** clears state to configure a fresh assessment."*

---

### Step 5: Flashcards, Audio Learning & Analytics (3:30 – 4:45)
**Action:** Navigate to **"Flashcards"**, then **"Audio Learning"**, then **"Analytics"**.
> *"For active recall, our **Flashcard Agent** synthesizes interactive 3D flip cards covering core definitions and formulas.*
> 
> *For auditory learners, the **Audio Learning Lab** leverages the browser's Web Speech API to narrate generated summaries with variable speed and voice pitch controls — requiring zero external API credits.*
> 
> *Finally, let's look at **Study Analytics**. The dashboard aggregates all quiz attempts into an Exponentially Weighted Moving Average (EWMA) curve. Notice how our performance across Classical Encryption is mapped visually using Recharts. If our score drops below 60%, the system automatically flags it as a Knowledge Deficit and suggests a remedial study plan."*

---

### Step 6: Conclusion (4:45 – 5:00)
**Speaker:** Varun D & Team
> *"Cognivora AI completes the full educational cycle: Ingest, Understand, Test, Review, and Master — all grounded strictly in verified syllabus documents. Thank you for your time, and we welcome your questions!"*
