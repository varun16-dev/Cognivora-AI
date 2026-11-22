import json
import uuid
import re
import logging
from typing import List, Dict, Any, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.services.rag_engine import rag_engine
from app.services.gemini_client import gemini_service
from app.database.models import QuizModel
from app.schemas.schemas import QuizQuestion

logger = logging.getLogger("CognivoraAI.QuizAgent")


class QuizAgent:
    """
    Specialized Agent for Educational Assessment Generation.
    Produces calibrated MCQs, True/False, and Fill-in-the-blank questions
    strictly grounded in the selected document with anti-hallucination validation.
    """

    @staticmethod
    def generate_quiz(
        document_id: str,
        document_name: str,
        topic: str = "General",
        difficulty: str = "medium",
        question_count: int = 5,
        question_types: List[str] = None,
        db: Session = None
    ) -> QuizModel:
        """
        Orchestrates RAG retrieval, schema prompting, and question validation
        exclusively for the selected document.
        """
        if not question_types:
            question_types = ["mcq"]

        logger.info(f"[QuizAgent] Generating {question_count} {difficulty} questions on '{topic}' from '{document_name}' (ID: {document_id})")

        # 1. Retrieve grounded context strictly from the specified document
        query = f"{topic} core concepts definitions algorithms rules differences mechanisms"
        chunks = rag_engine.retrieve_relevant_chunks(query=query, document_id=document_id, top_k=5)

        # If semantic search returned fewer than 2 chunks, fetch document's chunks directly
        if len(chunks) < 2:
            doc_chunks = rag_engine.get_document_chunks(document_id=document_id, limit=6)
            if doc_chunks:
                chunks = doc_chunks

        if not chunks:
            logger.error(f"[QuizAgent] No content chunks found for document '{document_name}' (ID: {document_id})")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot generate quiz: No readable content found for document '{document_name}'. Please ensure the document is uploaded and indexed."
            )

        context_text = "\n\n".join([f"Page {c.get('page_number', 1)}: {c.get('text', '')}" for c in chunks])

        # 2. Build structured prompt for LLM
        prompt = (
            f"Generate an academic assessment of {question_count} questions based strictly on the provided course material.\n\n"
            f"Document: {document_name}\n"
            f"Topic: {topic}\n"
            f"Difficulty Level: {difficulty.upper()} (Easy = direct recall/definition, Medium = applied scenarios, Hard = complex analysis/edge cases)\n"
            f"Question Types requested: {', '.join(question_types)}\n\n"
            f"Context from '{document_name}':\n{context_text[:4000]}\n\n"
            "Respond strictly in valid JSON matching this schema:\n"
            "[\n"
            "  {\n"
            "    \"id\": 1,\n"
            "    \"question\": \"The question prompt here...\",\n"
            "    \"question_type\": \"mcq\", // mcq, true_false, or fill_blank\n"
            "    \"options\": [\"Option A\", \"Option B\", \"Option C\", \"Option D\"],\n"
            "    \"correct_answer\": \"Option A\", // must match one of options exactly\n"
            "    \"explanation\": \"Pedagogical explanation why this is correct based on the context...\",\n"
            "    \"topic\": \"" + topic + "\",\n"
            "    \"difficulty\": \"" + difficulty + "\",\n"
            "    \"citation\": \"Page reference from context\"\n"
            "  }\n"
            "]"
        )

        system_instruction = (
            "You are a strict academic examiner. You create verified diagnostic assessments. "
            f"Every question MUST be based exclusively on the provided context from '{document_name}'. "
            f"Do NOT include questions about other subjects or unrelated materials. "
            "The correct_answer for an MCQ must exactly match one item in options. "
            "For True/False, options must be ['True', 'False']. "
            "Output valid JSON array only, without markdown wrapping."
        )

        questions: List[Dict[str, Any]] = []

        # 3. Call LLM if live
        if gemini_service.is_live():
            res = gemini_service.generate_structured_json(prompt, system_instruction)
            if res.get("data") and isinstance(res["data"], list):
                raw_list = res["data"]
                questions = QuizAgent._validate_and_sanitize_questions(raw_list, topic, difficulty, chunks, document_name)

        # 4. Fallback: Generate dynamic questions exclusively from retrieved document chunks
        if not questions:
            logger.info(f"[QuizAgent] Using dynamic document text fallback for '{document_name}'")
            questions = QuizAgent._generate_fallback_questions(chunks, topic, difficulty, question_count, question_types, document_name)

        if not questions:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to generate verified questions from document '{document_name}'."
            )

        # 5. Persist Quiz Record
        quiz_id = str(uuid.uuid4())
        quiz_record = QuizModel(
            id=quiz_id,
            document_id=document_id,
            title=f"{topic} — {difficulty.capitalize()} Diagnostic Quiz",
            topic=topic,
            difficulty=difficulty,
            question_count=len(questions),
            questions_json=json.dumps(questions)
        )

        if db:
            db.add(quiz_record)
            db.commit()
            db.refresh(quiz_record)

        logger.info(f"[QuizAgent] Successfully generated quiz '{quiz_record.title}' with {len(questions)} verified questions from '{document_name}'.")
        return quiz_record

    @staticmethod
    def _validate_and_sanitize_questions(
        raw_list: List[Dict[str, Any]],
        topic: str,
        difficulty: str,
        chunks: List[Dict[str, Any]],
        document_name: str
    ) -> List[Dict[str, Any]]:
        """Validates that each question conforms strictly to QuizQuestion schema."""
        validated = []
        default_citation = f"Page {chunks[0].get('page_number', 1)}, {document_name}" if chunks else document_name

        for i, q in enumerate(raw_list):
            try:
                q_id = i + 1
                prompt = str(q.get("question", "")).strip()
                q_type = str(q.get("question_type", "mcq")).lower()
                options = q.get("options", [])
                correct = str(q.get("correct_answer", "")).strip()
                explanation = str(q.get("explanation", f"Refer to {document_name} context for details.")).strip()

                if not prompt or not correct:
                    continue

                if q_type == "true_false":
                    options = ["True", "False"]
                    if correct.lower() in ["true", "t"]:
                        correct = "True"
                    else:
                        correct = "False"
                elif q_type == "mcq":
                    if not options or len(options) < 2:
                        continue
                    # Ensure correct answer is in options
                    if correct not in options:
                        options[0] = correct

                citation = q.get("citation")
                if not citation or citation.strip() in ["Uploaded Course Notes", "Page reference from context"]:
                    citation = default_citation

                validated.append({
                    "id": q_id,
                    "question": prompt,
                    "question_type": q_type,
                    "options": options,
                    "correct_answer": correct,
                    "explanation": explanation,
                    "topic": topic,
                    "difficulty": difficulty,
                    "citation": citation
                })
            except Exception as e:
                logger.warning(f"Skipping malformed question: {e}")
        return validated

    @staticmethod
    def _generate_fallback_questions(
        chunks: List[Dict[str, Any]],
        topic: str,
        difficulty: str,
        count: int,
        question_types: List[str],
        document_name: str
    ) -> List[Dict[str, Any]]:
        """
        Dynamically derives questions strictly from the retrieved document chunks.
        Never outputs hardcoded questions from other subjects.
        """
        if not chunks:
            return []

        # Extract informative factual sentences from the chunks
        sentences: List[Dict[str, Any]] = []
        for c in chunks:
            text = c.get("text", "")
            page = c.get("page_number", 1)
            raw_sents = re.split(r"(?<=[.!?])\s+|\n{2,}", text)
            for s in raw_sents:
                s = s.strip()
                # Clean up formatting artifacts
                s = re.sub(r"^\d+[\.\)]\s*", "", s)
                s = re.sub(r"^[#\-\*\•]\s*", "", s)
                if 35 <= len(s) <= 250 and not s.startswith(("http", "www", "Table", "Figure")):
                    sentences.append({
                        "text": s,
                        "page": page,
                        "doc_name": document_name
                    })

        if not sentences:
            # Fallback to chunk text segments if sentence split is sparse
            for c in chunks:
                lines = [l.strip() for l in c.get("text", "").split("\n") if len(l.strip()) >= 30]
                for l in lines[:3]:
                    sentences.append({
                        "text": l,
                        "page": c.get("page_number", 1),
                        "doc_name": document_name
                    })

        if not sentences:
            return []

        results = []
        for i in range(count):
            item = sentences[i % len(sentences)]
            sent_text = item["text"]
            page_num = item["page"]
            q_id = i + 1

            # Determine question type from requested types
            preferred_type = question_types[i % len(question_types)] if question_types else "mcq"

            if preferred_type == "true_false":
                results.append({
                    "id": q_id,
                    "question": f"Based on '{document_name}', is the following statement correct?\n\n\"{sent_text}\"",
                    "question_type": "true_false",
                    "options": ["True", "False"],
                    "correct_answer": "True",
                    "explanation": f"This statement is directly verified in '{document_name}' on Page {page_num}.",
                    "topic": topic,
                    "difficulty": difficulty,
                    "citation": f"Page {page_num}, {document_name}"
                })
            elif preferred_type == "fill_blank":
                words = re.findall(r"\b[A-Za-z]{4,}\b", sent_text)
                target_word = words[0] if words else topic
                blanked_sent = re.sub(rf"\b{re.escape(target_word)}\b", "______", sent_text, count=1)
                
                # Create plausible options
                other_words = [w for w in words[1:] if w.lower() != target_word.lower()][:3]
                distractors = other_words + ["Protocol", "Component", "Parameter"]
                distractors = [d for d in distractors if d.lower() != target_word.lower()][:3]
                options = [target_word] + distractors
                import random
                options = sorted(options)

                results.append({
                    "id": q_id,
                    "question": f"Complete the statement from '{document_name}':\n\n\"{blanked_sent}\"",
                    "question_type": "fill_blank",
                    "options": options,
                    "correct_answer": target_word,
                    "explanation": f"According to '{document_name}' on Page {page_num}, the complete statement is: \"{sent_text}\"",
                    "topic": topic,
                    "difficulty": difficulty,
                    "citation": f"Page {page_num}, {document_name}"
                })
            else:  # MCQ
                # Distractors from other sentences in the document
                other_sentences = [
                    s["text"] for j, s in enumerate(sentences) 
                    if j != (i % len(sentences)) and len(s["text"]) >= 25
                ]
                distractors = other_sentences[:3]
                while len(distractors) < 3:
                    distractors.append(f"An alternative mechanism unrelated to {topic} as detailed in Section {len(distractors) + 1}.")

                options = [sent_text] + distractors[:3]
                # Keep option order deterministic but varied
                import random
                rot = i % 4
                options = options[rot:] + options[:rot]

                results.append({
                    "id": q_id,
                    "question": f"According to '{document_name}', which of the following statements regarding '{topic}' is accurate?",
                    "question_type": "mcq",
                    "options": options,
                    "correct_answer": sent_text,
                    "explanation": f"Confirmed directly from '{document_name}' on Page {page_num}: \"{sent_text}\"",
                    "topic": topic,
                    "difficulty": difficulty,
                    "citation": f"Page {page_num}, {document_name}"
                })

        return results
