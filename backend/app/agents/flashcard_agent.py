import json
import uuid
import logging
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.services.rag_engine import rag_engine
from app.services.gemini_client import gemini_service
from app.database.models import FlashcardDeckModel
from app.schemas.schemas import Flashcard

logger = logging.getLogger("CognivoraAI.FlashcardAgent")


class FlashcardAgent:
    """
    Specialized Agent for Spaced-Repetition Flashcard Generation.
    Creates high-retention front/back concept cards from course text.
    """

    @staticmethod
    def generate_deck(
        document_id: str,
        document_name: str,
        topic: str = "General",
        card_count: int = 6,
        db: Session = None
    ) -> FlashcardDeckModel:
        """
        Retrieves course context and generates atomic revision flashcards.
        """
        logger.info(f"[FlashcardAgent] Generating {card_count} flashcards on '{topic}' from '{document_name}'")

        chunks = rag_engine.retrieve_relevant_chunks(
            query=f"{topic} key concepts terms definitions rules principles",
            document_id=document_id,
            top_k=4
        )
        context_text = "\n\n".join([c.get("text", "") for c in chunks])

        prompt = (
            f"Generate a deck of {card_count} spaced-repetition revision flashcards based on the following text.\n\n"
            f"Document: {document_name}\n"
            f"Topic: {topic}\n\n"
            f"Context:\n{context_text[:3000]}\n\n"
            "Format your output strictly as a JSON array of objects:\n"
            "[\n"
            "  {\n"
            "    \"id\": 1,\n"
            "    \"front\": \"Concise concept or question prompt (Front of card)\",\n"
            "    \"back\": \"Clear, high-retention definition or answer with key explanation (Back of card)\",\n"
            "    \"topic\": \"" + topic + "\",\n"
            "    \"difficulty\": \"medium\",\n"
            "    \"mastery_status\": \"learning\"\n"
            "  }\n"
            "]"
        )

        system_instruction = (
            "You are an educational flashcard author specializing in active recall. "
            "Write atomic, crisp front-back cards that test one discrete idea at a time. "
            "Output valid JSON array only."
        )

        cards = []
        if gemini_service.is_live():
            res = gemini_service.generate_structured_json(prompt, system_instruction)
            if res.get("data") and isinstance(res["data"], list):
                for i, c in enumerate(res["data"]):
                    front = str(c.get("front", "")).strip()
                    back = str(c.get("back", "")).strip()
                    if front and back:
                        cards.append({
                            "id": i + 1,
                            "front": front,
                            "back": back,
                            "topic": topic,
                            "difficulty": c.get("difficulty", "medium"),
                            "mastery_status": "learning"
                        })

        if not cards:
            cards = FlashcardAgent._generate_fallback_cards(chunks, topic, card_count, document_name)

        deck_id = str(uuid.uuid4())
        deck_record = FlashcardDeckModel(
            id=deck_id,
            document_id=document_id,
            title=f"{topic} Revision Deck",
            topic=topic,
            cards_json=json.dumps(cards)
        )

        if db:
            db.add(deck_record)
            db.commit()
            db.refresh(deck_record)

        logger.info(f"[FlashcardAgent] Successfully created deck '{deck_record.title}' with {len(cards)} cards.")
        return deck_record

    @staticmethod
    def _generate_fallback_cards(
        chunks: List[Dict[str, Any]],
        topic: str,
        count: int,
        document_name: str
    ) -> List[Dict[str, Any]]:
        """Dynamically generates active recall flashcards strictly from document chunks."""
        import re
        sentences = []
        for c in chunks:
            text = c.get("text", "")
            raw = re.split(r"(?<=[.!?])\s+|\n{2,}", text)
            for s in raw:
                s = s.strip()
                if 30 <= len(s) <= 200 and not s.startswith(("#", "-", "*", "http")):
                    sentences.append((s, c.get("page_number", 1)))

        results = []
        for i in range(count):
            if sentences:
                sent, page = sentences[i % len(sentences)]
                words = re.findall(r"\b[A-Za-z]{4,}\b", sent)
                key_term = words[0] if words else topic
                results.append({
                    "id": i + 1,
                    "front": f"What does '{document_name}' state regarding {key_term} (Page {page})?",
                    "back": sent,
                    "topic": topic,
                    "difficulty": "medium",
                    "mastery_status": "learning"
                })
            else:
                results.append({
                    "id": i + 1,
                    "front": f"Core concept of {topic} in {document_name}",
                    "back": f"Refer to {document_name} course notes for detailed mechanisms and definitions.",
                    "topic": topic,
                    "difficulty": "easy",
                    "mastery_status": "learning"
                })
        return results
