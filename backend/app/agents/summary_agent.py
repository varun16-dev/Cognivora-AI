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
            content, key_points = SummaryAgent._generate_fallback_summary(chunks, topic, mode, document_name)

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
    def _generate_fallback_summary(chunks: List[Dict[str, Any]], topic: str, mode: str, doc_name: str) -> tuple[str, List[str]]:
        import re
        sentences = []
        for c in chunks:
            text = c.get("text", "")
            raw = re.split(r"(?<=[.!?])\s+|\n{2,}", text)
            for s in raw:
                s = s.strip()
                if 25 <= len(s) <= 220 and not s.startswith(("#", "-", "*", "http")):
                    sentences.append(s)

        key_points = sentences[:5] if sentences else [f"Review core principles of {topic} in {doc_name}."]

        summary_body = "\n\n".join(sentences[:4]) if sentences else f"Detailed study material for {topic} derived from {doc_name}."

        content = (
            f"# {topic}: Academic Summary\n\n"
            f"**Source Document:** {doc_name}\n\n"
            f"### Overview & Key Concepts\n"
            f"{summary_body}\n\n"
            f"### High-Yield Key Points\n"
            + "\n".join([f"- {kp}" for kp in key_points])
        )
        return content, key_points
