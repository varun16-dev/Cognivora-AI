# Cognivora AI — 3–5 Minute Demo Video Recording Guide & Script

**Author:** Cognivora AI Team (Varun D, Sindhuja S, Mohith S)  
**Status:** **SCRIPT PREPARED — PENDING STUDENT RECORDING**  
*Note: As per Capabl guidelines, this script and checklist are prepared for the student to record their live screen.*

---

## 1. Quick Recording Setup on Windows (Zero Installation Required)

You have two fast, high-quality options on Windows 10/11:

### Option A: Windows Snipping Tool / Game Bar (Built-in)
1. **Shortcut:** Press `Win + Alt + R` to start recording immediately, or press `Win + Shift + S` and select the **Video** icon to select your browser window.
2. Ensure your microphone is enabled in the recording widget.
3. Recordings are automatically saved in `C:\Users\<Username>\Videos\Captures`.

### Option B: OBS Studio (If installed)
1. Add a **Window Capture** source targeting your browser at `http://localhost:5173`.
2. Set output resolution to `1920x1080` (1080p).
3. Test microphone levels.

---

## 2. Pre-Recording Checklist

- [ ] Backend is running in PowerShell:  
  `python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload`
- [ ] Frontend is running in a second PowerShell terminal:  
  `cd frontend ; npm run dev`
- [ ] Browser window open at: `http://localhost:5173`
- [ ] Browser zoom level set to 100% or 110% for crisp readability.
- [ ] Sample document ready in `data/sample_documents/os_deadlocks_and_scheduling.txt` or a PDF of your choice.

---

## 3. Minute-by-Minute Recording Script

### 0:00 – 0:45 | Scene 1: Introduction, Problem & Team
* **Screen Display:** Dashboard view at `http://localhost:5173`.
* **Action:** Keep the mouse steady over the Dashboard overview.
* **Voiceover:**
  > "Hello everyone. Welcome to our Capabl Agentic AI project presentation of **Cognivora AI**, an autonomous educational content generator.
  > Our team consists of three members: Varun D as Team Lead & AI Integration, Sindhuja S as Lead Frontend & UI/UX Engineer, and Mohith S as Lead Backend & Database Engineer.
  > Today, college students spend up to 40% of their study time passively highlighting 50-to-100-page textbooks without active recall, and general-purpose chatbots often invent facts or hallucinate citations. Cognivora AI solves this by transforming static course documents into an active, multi-modal, adaptive learning experience."

---

### 0:45 – 1:30 | Scene 2: Multi-Agent Architecture & Tech Stack
* **Screen Display:** Click on **AI Study Chat** (`/chat`), then point to the **Agent Decision Inspector**.
* **Action:** Highlight the model indicator in the header ("Gemini 2.5 Flash / Demo Mode") and the sidebar tabs.
* **Voiceover:**
  > "Cognivora AI is built on a genuine multi-agent hierarchy rather than a simple chatbot prompt.
  > Our **Coordinator Agent** uses LangChain tools to classify student intent and dynamically dispatch tasks to four specialized agents:
  > The **Document Agent** for semantic chunking and ChromaDB indexing, the **Quiz Agent** for Bloom-calibrated assessments, the **Flashcard Agent** for active recall, and the **Summary Agent** for multi-mode note synthesis.
  > Our technology stack pairs a responsive React 19 and Tailwind CSS frontend with a high-performance FastAPI backend, Google Gemini 2.5 Flash, ChromaDB vector storage, and SQLite for study history."

---

### 1:30 – 2:15 | Scene 3: Document Upload & Syllabus Hierarchy
* **Screen Display:** Click on **Upload Documents** (`/documents`).
* **Action:** Drag and drop `os_deadlocks_and_scheduling.txt` or a PDF into the drop zone. Show the progress bar, the chunk counter, and click the **"View Outline"** button to open the detected syllabus modal.
* **Voiceover:**
  > "Let's look at the document ingestion pipeline. On the Uploads page, students can drop PDF, DOCX, or TXT documents.
  > Our Document Agent extracts the text, builds 650-character semantic chunks with 120-character sliding overlap, indexes them into ChromaDB, and automatically detects unit titles and chapter outlines as shown in this syllabus inspector modal."

---

### 2:15 – 3:00 | Scene 4: Grounded Study Chat & Anti-Hallucination Guardrail
* **Screen Display:** Navigate to **AI Study Chat** (`/chat`).
* **Action:**
  1. Select the **Standard Academic** mode.
  2. Send the message: *"What are the 4 conditions required for a deadlock?"*
  3. Show the response, hover over the **Source Citation Pill** showing page and similarity score.
  4. Click the **"Agent Decision Inspector"** to show the real-time reasoning trace.
  5. Send an unrelated query: *"What is the capital of Iceland?"* to demonstrate the strict refusal guardrail.
* **Voiceover:**
  > "In the AI Study Chat, questions are strictly grounded in the student's uploaded notes.
  > Here, when we ask about deadlock conditions, notice how the response cites the exact page and document name with cosine similarity. Clicking the Agent Inspector shows the Coordinator's tool selection in real time.
  > Furthermore, when we ask an out-of-scope question like the capital of Iceland, our anti-hallucination guardrail strictly refuses to answer without fabricating citations."

---

### 3:00 – 3:45 | Scene 5: Quiz Station, Flashcards & Audio Learning
* **Screen Display:** Move to **Quiz Generator** (`/quiz`), then **Flashcards** (`/flashcards`), then **Summaries** (`/summaries`).
* **Action:**
  1. Click *"Generate Practice Quiz"*, answer 2 questions, click *"Submit & Grade Quiz"*.
  2. Show the instant percentage score and click **"Export Quiz Sheet"** to download the Markdown file.
  3. Switch to **Flashcards**, click a card to show the 3D flip animation, and rate it *"Mastered"*.
  4. Switch to **AI Summaries**, generate an *"Exam Cram"* summary, and click **"Listen Spoken Lesson"** to jump to the Audio Learning Lab.
  5. In **Audio Learning**, click **Play** to demonstrate the browser Web Speech API voice synthesis and waveform visualizer.
* **Voiceover:**
  > "Next, our Quiz Generator generates calibrated assessments with instant grading, question-by-question explanations, and a one-click Markdown study sheet export.
  > Over on Flashcards, students study active recall with smooth 3D flip cards and confidence ratings.
  > Our Summary Agent generates five pedagogical styles, including exam cram sheets. With one click, students can send any summary to the Audio Learning Lab to listen to spoken lessons with customizable speed and pitch."

---

### 3:45 – 4:30 | Scene 6: Study Analytics & Conclusion
* **Screen Display:** Navigate to **Study Analytics** (`/analytics`).
* **Action:** Scroll through the Recharts topic mastery bar chart, the score trajectory line chart, and highlight the weak-topic alert cards (<60%).
* **Voiceover:**
  > "Finally, our Study Analytics page uses an Exponentially Weighted Moving Average formula to track topic mastery over time.
  > Topics scoring below 60% are flagged as deficit areas, automatically generating focused revision recommendations.
  > All 11 integration test cases pass, the frontend compiles with zero errors, and complete 8-week documentation is live in our GitHub repository.
  > Thank you for reviewing Cognivora AI!"

---

## 4. Post-Recording Steps

1. Review your recorded MP4 file for clear audio and smooth transitions.
2. Upload the video to **YouTube (Unlisted)** or **Google Drive (Anyone with link can view)**.
3. Paste the shareable video link into the README under Section 19.
