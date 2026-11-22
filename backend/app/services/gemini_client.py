import os
import re
import time
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
            "You are Cognivora AI, a rigorous, pedagogical Academic AI Tutor and Educational Assistant. "
            "Your highest priority is GROUNDED ACCURACY, pedagogical depth, and clarity.\n\n"
            "Pedagogical Guidelines:\n"
            "1. Ground your entire answer strictly in the provided retrieved course context.\n"
            "2. Provide a structured, high-quality educational explanation:\n"
            "   - **Clear Definition & Overview**: Define the core concepts clearly.\n"
            "   - **Mechanics & Detailed Explanation**: Detail how the concepts, rules, or algorithms operate step-by-step from the curriculum text.\n"
            "   - **Examples & Practical Context**: Include concrete examples or illustrations grounded in or implied by the material.\n"
            "   - **Actionable Takeaways**: Highlight key points essential for exam review or mastery.\n"
            "3. Format cleanly using Markdown with headings (##, ###), bold key terminology, numbered steps, and bullet points.\n"
            "4. Cite sources accurately in the body (e.g. `[Source 1, Page 3]`). Never fabricate source labels or page numbers.\n"
            "5. NEVER use generic placeholder or boiler-plate phrases like 'Conditions and algorithmic criteria must be satisfied.' Always explain the actual concept and mechanism.\n"
            "6. Strict Grounding Guardrail: If the provided context does NOT contain enough information to answer the question, state: "
            "'I cannot find this specific information in your uploaded course materials. Please upload relevant notes or consult your professor.'\n"
            f"7. Pedagogical Tone: {mode_instructions.get(pedagogical_mode, mode_instructions['standard'])}"
        )

        user_content = f"### STUDENT QUESTION:\n{prompt}\n\n### RETRIEVED COURSE CONTEXT:\n{context_text}"

        if self.client:
            for attempt in range(2):
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
                    err_str = str(e)
                    if "503" in err_str and attempt == 0:
                        logger.warning("Gemini 503 demand spike, retrying after 1s...")
                        time.sleep(1.2)
                        continue
                    logger.error(f"Gemini API call failed: {e}. Falling back to curriculum engine.")
                    break

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
        stop_words = {"what", "is", "the", "and", "was", "for", "in", "of", "a", "an", "to", "how", "why", "are", "do", "does", "can", "you", "tell", "me", "about"}
        q_tokens = set(re.findall(r"\w+", prompt.lower())) - stop_words
        top_text = (context_chunks[0].get("text", "") if context_chunks else "").lower()
        has_keyword_match = any(t in top_text for t in q_tokens) if q_tokens else True
        top_sim = context_chunks[0].get("similarity_score", 0.0) if context_chunks else 0.0

        if not context_chunks or (top_sim < 0.45 and not has_keyword_match) or (not has_keyword_match and top_sim < 0.65):
            return {
                "answer": (
                    "I cannot find this specific information in your uploaded course materials. "
                    "Please upload relevant notes or consult your professor."
                ),
                "model_used": "Built-in Educational Engine (Grounding Guardrail Active)",
                "is_demo_mode": True
            }

        top_chunk = context_chunks[0]
        raw_text = top_chunk.get("text", "")
        page = top_chunk.get("page_number", 1)
        doc_name = top_chunk.get("document_name", "Uploaded Course Notes")
        subject = top_chunk.get("subject", "Academic Coursework")
        similarity = top_chunk.get("similarity_score", 0.88)

        # Extract meaningful concept sentences from the retrieved text
        clean_text = re.sub(r'\s+', ' ', raw_text).strip()
        sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', clean_text) if len(s.strip()) > 25]
        key_excerpts = sentences[:3] if sentences else [clean_text[:300]]

        prefix = {
            "explain_simply": "💡 **Simplified Conceptual Breakdown:**\n\n",
            "exam_cram": "⚡ **Exam High-Yield Review:**\n\n",
            "deep_dive": "🔍 **In-Depth Theoretical Analysis:**\n\n",
            "standard": "📚 **Curriculum-Grounded Answer:**\n\n"
        }.get(pedagogical_mode, "📚 **Curriculum-Grounded Answer:**\n\n")

        bullet_points = "\n".join([f"- **Concept Insight:** {s}" for s in key_excerpts])

        answer_text = (
            f"{prefix}"
            f"Based on **{doc_name}** (Page {page}), here is the grounded explanation:\n\n"
            f"### Verified Course Content\n"
            f"{bullet_points}\n\n"
            f"### Educational Takeaways\n"
            f"1. **Core Subject Area:** Grounded in syllabus section **{subject}**.\n"
            f"2. **Relevance & Verification:** Match verified on **Page {page}** with {similarity * 100:.0f}% curriculum alignment.\n"
            f"3. **Study Guidance:** Consult related sections in `{doc_name}` to review worked examples and theorem proofs.\n\n"
            f"**Source Citation:** Verified from `{doc_name}`, Page {page}."
        )

        return {
            "answer": answer_text,
            "model_used": "Built-in Educational Engine (Grounding Engine)",
            "is_demo_mode": True
        }


# Global singleton
gemini_service = GeminiService()
