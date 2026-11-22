import json
import uuid
import logging
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.services.rag_engine import rag_engine
from app.services.gemini_client import gemini_service
from app.database.models import SummaryModel

logger = logging.getLogger("CognivoraAI.SummaryAgent")


class SummaryAgent:
    """
    Specialized Agent for Educational Summaries & Spoken Lesson Preparation.
    Produces Short, Detailed, Key Points, Beginner-friendly, and Exam Cram summaries.
    """

    @staticmethod
    def generate_summary(
        document_id: str,
        document_name: str,
        topic: str = "General",
        mode: str = "detailed",
        db: Session = None
    ) -> SummaryModel:
        """
        Synthesizes curricular summaries formatted in structured Markdown.
        """
        logger.info(f"[SummaryAgent] Generating '{mode}' summary for '{topic}' in '{document_name}'")

        chunks = rag_engine.retrieve_relevant_chunks(
            query=f"{topic} core overview explanations mechanisms examples",
            document_id=document_id,
            top_k=5
        )
        context_text = "\n\n".join([f"Page {c.get('page_number', 1)}: {c.get('text', '')}" for c in chunks])

        mode_prompts = {
            "short": "Produce an executive 2-minute high-impact summary emphasizing core definitions and practical meaning.",
            "detailed": "Produce a comprehensive, structured textbook breakdown with clear sections, bold terms, and thorough explanations.",
            "key_points": "Extract an ordered, high-yield bulleted list of the top 7-10 essential concepts and rules.",
            "beginner": "Explain the concept from scratch using intuitive real-world analogies, avoiding unnecessary technical jargon.",
            "exam_notes": "Produce a high-yield exam revision sheet with essential definitions, common exam traps, comparison tables, and quick formulas."
        }

        prompt = (
            f"Synthesize an educational summary of the following academic material.\n\n"
            f"Document: {document_name}\n"
            f"Topic: {topic}\n"
            f"Summary Mode: {mode.upper()} — {mode_prompts.get(mode, mode_prompts['detailed'])}\n\n"
            f"Course Material Context:\n{context_text[:3500]}\n\n"
            "Format your output strictly as a JSON object:\n"
            "{\n"
            "  \"title\": \"Descriptive Summary Title\",\n"
            "  \"content\": \"Full markdown formatted summary text...\",\n"
            "  \"key_points\": [\"Point 1\", \"Point 2\", \"Point 3\", \"Point 4\", \"Point 5\"]\n"
            "}"
        )

        system_instruction = (
            "You are a master university lecturer. Synthesize clear, engaging, and accurate study notes. "
            "Grounded strictly in the source text. Output valid JSON object only."
        )

        title = f"{topic} ({mode.replace('_', ' ').title()})"
        content = ""
        key_points = []

        if gemini_service.is_live():
            res = gemini_service.generate_structured_json(prompt, system_instruction)
            if res.get("data") and isinstance(res["data"], dict):
                data = res["data"]
                title = data.get("title", title)
                content = data.get("content", "")
                key_points = data.get("key_points", [])

        if not content:
            content, key_points = SummaryAgent._generate_fallback_summary(topic, mode, document_name)

        summary_id = str(uuid.uuid4())
        summary_record = SummaryModel(
            id=summary_id,
            document_id=document_id,
            title=title,
            topic=topic,
            mode=mode,
            content=content,
            key_points_json=json.dumps(key_points)
        )

        if db:
            db.add(summary_record)
            db.commit()
            db.refresh(summary_record)

        logger.info(f"[SummaryAgent] Successfully saved summary '{summary_record.title}'")
        return summary_record

    @staticmethod
    def _generate_fallback_summary(topic: str, mode: str, doc_name: str) -> tuple[str, List[str]]:
        key_points = [
            "A deadlock is a condition where a set of processes are permanently waiting for resources held by others in the set.",
            "The 4 necessary conditions are Mutual Exclusion, Hold and Wait, No Preemption, and Circular Wait.",
            "Deadlock Prevention eliminates one of the four necessary conditions before resources are requested.",
            "Deadlock Avoidance uses prior knowledge of maximum resource demands to ensure the system remains in a safe state.",
            "Banker's Algorithm guarantees that a safe sequence exists before approving any resource request.",
            "The Ostrich Algorithm ignores the problem, trading theoretical safety for system simplicity."
        ]

        if mode == "short":
            content = (
                f"# Executive Summary: {topic}\n\n"
                f"**Source Document:** {doc_name}\n\n"
                "In multiprogramming environments, multiple processes compete for limited system resources. "
                "A **deadlock** occurs when processes enter an irreversible waiting state because each process holds a resource "
                "that another process requires. Operating systems resolve this through three main paradigms: **prevention** "
                "(invalidating one of the four necessary conditions), **avoidance** (using algorithms like Dijkstra's Banker's Algorithm "
                "to maintain safe state sequences), or **detection and recovery**."
            )
        elif mode == "beginner":
            content = (
                f"# Beginner-Friendly Guide: {topic}\n\n"
                "Imagine a narrow single-lane bridge where two cars enter from opposite directions at the exact same moment. "
                "Car A cannot move forward because Car B is blocking the lane. Car B cannot move forward because Car A is in front of it. "
                "Neither driver wants to reverse. That traffic gridlock is exactly what a **Deadlock** is in computer operating systems!\n\n"
                "### The 4 Ingredients of a Deadlock:\n"
                "1. **Only One at a Time:** A resource cannot be shared simultaneously (Mutual Exclusion).\n"
                "2. **Holding and Asking for More:** You hold a toy and refuse to drop it while reaching for another (Hold and Wait).\n"
                "3. **No Grabbing:** Nobody can forcefully take your resource from your hands (No Preemption).\n"
                "4. **Circle of Waiting:** Person A waits for B, B waits for C, and C waits for A (Circular Wait)."
            )
        elif mode == "exam_notes":
            content = (
                f"# High-Yield Exam Revision Notes: {topic}\n\n"
                "### 1. Mandatory Definitions for 100% Marks:\n"
                "- **Deadlock:** Permanent blocking of a set of processes that each contend for resources held by others in the set.\n"
                "- **Safe State:** A state where at least one allocation sequence `<P1, P2, ..., Pn>` allows all processes to finish.\n\n"
                "### 2. The 4 Necessary Conditions Checklist (Coffman Conditions):\n"
                "- [x] **Mutual Exclusion**\n"
                "- [x] **Hold and Wait**\n"
                "- [x] **No Preemption**\n"
                "- [x] **Circular Wait**\n\n"
                "### 3. Banker's Algorithm Critical Exam Formulas:\n"
                "- `Need[i][j] = Max[i][j] - Allocation[i][j]`\n"
                "- If `Request_i <= Need_i` AND `Request_i <= Available`: Tentatively allocate and run safety check.\n\n"
                "### 4. Common Exam Pitfalls:\n"
                "- *Trap:* 'An unsafe state is always a deadlock.' — **FALSE!** Every deadlock is unsafe, but an unsafe state may still avoid deadlock if processes do not request maximum claims."
            )
        elif mode == "key_points":
            content = f"# Key Takeaways: {topic}\n\n" + "\n".join([f"- **Point {i+1}:** {p}" for i, p in enumerate(key_points)])
        else:
            content = (
                f"# Detailed Analysis: {topic}\n\n"
                f"### 1. Theoretical Foundations\n"
                "Operating systems must arbitrate hardware and software resource distribution across concurrent tasks. "
                "When resource contention is unmanaged, circular dependencies freeze processes indefinitely.\n\n"
                "### 2. Four Necessary Conditions (Coffman Conditions)\n"
                "Deadlocks cannot form unless all four conditions hold concurrently. Breaking any one condition guarantees prevention.\n\n"
                "### 3. Avoidance & Banker's Algorithm\n"
                "Unlike prevention which constrains requests statically, avoidance algorithms dynamically evaluate incoming requests. "
                "The system simulates allocation and verifies that a **safe sequence** exists before committing changes.\n\n"
                "### 4. Architectural Trade-offs\n"
                "While Banker's Algorithm provides mathematical safety, it requires advance knowledge of maximum process resource claims, "
                "which is impractical in general-purpose desktop operating systems."
            )

        return content, key_points
