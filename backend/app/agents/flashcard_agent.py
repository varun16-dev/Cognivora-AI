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
            cards = FlashcardAgent._generate_fallback_cards(topic, card_count)

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
    def _generate_fallback_cards(topic: str, count: int) -> List[Dict[str, Any]]:
        bank = [
            {
                "front": "What is a Deadlock in Operating Systems?",
                "back": "A situation where a set of processes are permanently blocked because each process is holding a resource and waiting for another resource held by another process in the same set.",
                "topic": "Deadlocks",
                "difficulty": "easy"
            },
            {
                "front": "What are the 4 Necessary Conditions for Deadlock?",
                "back": "1. Mutual Exclusion\n2. Hold and Wait\n3. No Preemption\n4. Circular Wait\nAll four must hold simultaneously for a deadlock to exist.",
                "topic": "Conditions",
                "difficulty": "medium"
            },
            {
                "front": "How does Deadlock Prevention differ from Deadlock Avoidance?",
                "back": "Prevention eliminates at least one of the 4 necessary conditions before requests occur. Avoidance dynamically checks resource allocation requests using priori knowledge to ensure the system never leaves a safe state.",
                "topic": "Prevention vs Avoidance",
                "difficulty": "hard"
            },
            {
                "front": "What is a 'Safe State' in Banker's Algorithm?",
                "back": "A state where there exists a sequence <P1, P2, ..., Pn> such that each process can satisfy its maximum remaining resource requests using available resources plus resources held by prior processes.",
                "topic": "Banker's Algorithm",
                "difficulty": "medium"
            },
            {
                "front": "What is the 'Ostrich Algorithm'?",
                "back": "The strategy of ignoring the deadlock problem entirely, assuming deadlocks occur rarely and that the system recovery overhead is lower than continuous prevention algorithms.",
                "topic": "Handling Strategies",
                "difficulty": "easy"
            },
            {
                "front": "What is a Resource Allocation Graph (RAG)?",
                "back": "A directed graph with process nodes and resource nodes. Request edges go from Process -> Resource; Assignment edges go from Resource -> Process. A cycle indicates deadlock if single instance per resource.",
                "topic": "Graph Modeling",
                "difficulty": "hard"
            }
        ]

        results = []
        for i in range(count):
            item = bank[i % len(bank)].copy()
            item["id"] = i + 1
            item["mastery_status"] = "learning"
            results.append(item)
        return results
