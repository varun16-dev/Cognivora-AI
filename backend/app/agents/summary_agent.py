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
        import re
        topic = re.sub(
            r"^[\s#\-\–\—\*\•\d\.\/:]*(?:Module|Chapter|Unit|Section)?[\s\-\–\—\d:\.]*",
            "",
            topic,
            flags=re.IGNORECASE
        ).strip() or topic

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

        clean_topic = re.sub(
            r"^[\s#\-\–\—\*\•\d\.\/:]*(?:Module|Chapter|Unit|Section)?[\s\-\–\—\d:\.]*",
            "",
            topic,
            flags=re.IGNORECASE
        ).strip() or topic

        sentences = []
        for c in chunks:
            text = c.get("text", "")
            raw = re.split(r"(?<=[.!?])\s+|\n{2,}", text)
            for s in raw:
                cleaned = re.sub(r"\s+", " ", s).strip()
                # Exclude slide headers, author names, course identifiers, or fragments
                if re.search(r"\b(Dr\.|Prof\.|Professor|Prepared by|Module\s*[\-–—\d]|Unit\s*\d+|Chapter\s*\d+|BAD\d+|BAI\d+|Data Security and Privacy)\b", cleaned, re.IGNORECASE):
                    continue
                # Require complete sentence structure
                if len(cleaned.split()) >= 6 and (cleaned.endswith((".", "!", "?")) or len(cleaned) >= 50):
                    if cleaned not in sentences and not cleaned.startswith(("#", "-", "*", "http")):
                        sentences.append(cleaned)

        if len(sentences) >= 6:
            overview_sentences = sentences[:3]
            key_point_sentences = sentences[3:8]
        elif len(sentences) >= 3:
            overview_sentences = sentences[:2]
            key_point_sentences = sentences[2:]
        elif sentences:
            overview_sentences = sentences
            key_point_sentences = [f"Primary takeaway: {s}" for s in sentences]
        else:
            overview_sentences = [f"This academic lecture material focuses on the foundational principles, design criteria, and architectural standards for {clean_topic}."]
            key_point_sentences = [
                f"Understand standard protocols and regulatory requirements for {clean_topic}.",
                f"Evaluate operational security trade-offs as detailed in {doc_name}."
            ]

        summary_body = "\n\n".join(overview_sentences)
        key_points = key_point_sentences

        content = (
            f"# {clean_topic}: Academic Summary\n\n"
            f"**Source Document:** {doc_name}\n\n"
            f"### Overview & Key Concepts\n"
            f"{summary_body}\n\n"
            f"### High-Yield Key Points\n"
            + "\n".join([f"- {kp}" for kp in key_points])
        )
        return content, key_points
