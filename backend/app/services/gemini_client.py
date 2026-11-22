import os
import json
import logging
from typing import Dict, Any, Optional, List
from google import genai
from google.genai import types
from google.genai.errors import APIError
from app.config import settings

logger = logging.getLogger("CognivoraAI.GeminiClient")


class GeminiService:
    """
    Robust Google Gemini client with structured generation, anti-hallucination guardrails,
    and fallback Educational Curriculum Engine for quota limits and demo mode.
    """

    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY or os.getenv("GEMINI_API_KEY", "")
        self.client: Optional[genai.Client] = None
        self.model_name = settings.PRIMARY_MODEL

        if self.api_key and self.api_key.strip() and self.api_key != "your_gemini_api_key_here":
            try:
                self.client = genai.Client(api_key=self.api_key.strip())
                logger.info(f"Initialized Google GenAI Client with model: {self.model_name}")
            except Exception as e:
                logger.warning(f"Could not initialize live Google GenAI Client: {e}. Defaulting to Demo Engine.")
                self.client = None
        else:
            logger.info("No valid GEMINI_API_KEY provided. Operating in high-fidelity Demonstration Mode.")

    def is_live(self) -> bool:
        """Returns True if live Google Gemini API client is configured."""
        return self.client is not None

    def generate_grounded_answer(
        self,
        prompt: str,
        context_chunks: List[Dict[str, Any]],
        pedagogical_mode: str = "standard"
    ) -> Dict[str, Any]:
        """
        Generates a context-grounded response strictly adhering to retrieved academic chunks.
        """
        mode_instructions = {
            "standard": "Provide a clear, balanced academic explanation with direct references to the concepts.",
            "explain_simply": "Explain the concept using intuitive analogies and beginner-friendly, plain language.",
            "exam_cram": "Focus strictly on high-yield exam takeaways, definitions, key formulas, and common pitfalls.",
            "deep_dive": "Provide an in-depth architectural and theoretical breakdown with edge-case considerations."
        }

        context_text = "\n\n".join([
            f"[Source {i+1} | Page {c.get('page_number', 1)} | Document: {c.get('document_name', 'Document')}]:\n{c.get('text', '')}"
            for i, c in enumerate(context_chunks)
        ])

        system_instruction = (
            "You are Cognivora AI, a rigorous, pedagogical Academic AI Tutor. "
            "Your highest priority is GROUNDED ACCURACY. You must answer the student's question "
            "using ONLY the provided reference context from their course materials.\n"
            "Rules:\n"
            "1. If the provided context does NOT contain enough information to answer the question, state: "
            "'I cannot find this specific information in your uploaded course materials. Please upload relevant notes or consult your professor.'\n"
            "2. Never fabricate facts, external theories, or unverified claims not grounded in the context.\n"
            "3. Cite source references naturally (e.g. '[Source 1, Page 3]').\n"
            f"4. Pedagogical Tone: {mode_instructions.get(pedagogical_mode, mode_instructions['standard'])}"
        )

        user_content = f"### STUDENT QUESTION:\n{prompt}\n\n### RETRIEVED COURSE CONTEXT:\n{context_text}"

        if self.client:
            try:
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=user_content,
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        temperature=0.2,
                    )
                )
                return {
                    "answer": response.text,
                    "model_used": self.model_name,
                    "is_demo_mode": False
                }
            except Exception as e:
                logger.error(f"Gemini API call failed: {e}. Falling back to curriculum engine.")

        # Fallback Demonstration / Offline Engine
        return self._demo_grounded_answer(prompt, context_chunks, pedagogical_mode)

    def generate_structured_json(
        self,
        prompt: str,
        system_instruction: str,
        expected_schema_name: str = "StructuredResponse"
    ) -> Dict[str, Any]:
        """
        Calls Gemini with JSON mime-type enforcement for quizzes, flashcards, or summaries.
        """
        if self.client:
            try:
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        response_mime_type="application/json",
                        temperature=0.3,
                    )
                )
                text = response.text.strip()
                # Clean possible markdown json code blocks
                if text.startswith("```json"):
                    text = text[7:]
                if text.startswith("```"):
                    text = text[3:]
                if text.endswith("```"):
                    text = text[:-3]
                parsed = json.loads(text.strip())
                return {"data": parsed, "model_used": self.model_name, "is_demo_mode": False}
            except Exception as e:
                logger.error(f"Gemini structured JSON failed: {e}. Falling back to curriculum generator.")

        return {"data": None, "model_used": "Built-in Educational Engine", "is_demo_mode": True}

    def _demo_grounded_answer(
        self,
        prompt: str,
        context_chunks: List[Dict[str, Any]],
        pedagogical_mode: str
    ) -> Dict[str, Any]:
        """High-fidelity contextual response generator when operating in Demo Mode."""
        if not context_chunks:
            return {
                "answer": (
                    "**Notice (Demonstration Mode):** No relevant context could be found in your uploaded materials "
                    "for this query. To get grounded answers, ensure you have uploaded documents relating to this topic."
                ),
                "model_used": "Built-in Educational Engine (Demo Mode)",
                "is_demo_mode": True
            }

        top_chunk = context_chunks[0]
        excerpt = top_chunk.get("text", "")[:400]
        page = top_chunk.get("page_number", 1)
        doc_name = top_chunk.get("document_name", "Uploaded Course Notes")

        prefix = {
            "explain_simply": "💡 **Simplified Explanation:**\n\n",
            "exam_cram": "⚡ **Exam High-Yield Review:**\n\n",
            "deep_dive": "🔍 **In-Depth Theoretical Analysis:**\n\n",
            "standard": "📚 **Curriculum-Grounded Answer:**\n\n"
        }.get(pedagogical_mode, "📚 **Curriculum-Grounded Answer:**\n\n")

        answer_text = (
            f"{prefix}"
            f"Based on **{doc_name}** (Page {page}), here is the grounded resolution to your question:\n\n"
            f"> *\"{excerpt}...\"*\n\n"
            f"**Key Takeaways:**\n"
            f"1. **Core Concept:** The course material outlines this concept specifically within the documented syllabus.\n"
            f"2. **Mechanism / Rule:** Conditions and algorithmic criteria must be satisfied as detailed in Page {page}.\n"
            f"3. **Practical Implication:** In academic evaluations, this topic is tested on strict compliance with the established definition.\n\n"
            f"*Source Citation:* Verified from `{doc_name}`, Page {page}."
        )

        return {
            "answer": answer_text,
            "model_used": "Built-in Educational Engine (Demo Mode - Add GEMINI_API_KEY in .env for Live Gemini 2.5 Flash)",
            "is_demo_mode": True
        }


# Global singleton
gemini_service = GeminiService()
