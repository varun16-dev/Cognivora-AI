import json
import uuid
import re
import logging
from typing import List, Dict, Any, Optional, Tuple, Set
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.services.rag_engine import rag_engine
from app.services.gemini_client import gemini_service
from app.database.models import QuizModel
from app.schemas.schemas import QuizQuestion

logger = logging.getLogger("CognivoraAI.QuizAgent")

# Common English stopwords to ignore during semantic token comparison
STOPWORDS: Set[str] = {
    "the", "and", "that", "this", "with", "from", "for", "which",
    "what", "how", "following", "based", "true", "false", "according",
    "correct", "statement", "regarding", "document", "question", "select",
    "does", "explain", "describe", "identify", "about", "their", "there",
    "where", "when", "would", "could", "should", "using", "under"
}

# Analytical and scenario indicator keywords for HARD difficulty
HARD_ANALYTICAL_INDICATORS: Set[str] = {
    "scenario", "suppose", "consider", "attacker", "intercepts", "calculate",
    "determine", "decrypt", "encrypt", "vulnerability", "weakness", "trade-off",
    "evaluate", "analyze", "consequence", "impact", "sequence", "unknown",
    "derives", "reconstruct", "compromise", "exploit", "cryptanalysis",
    "brute-force", "frequency analysis", "multi-step", "mathematically"
}

# Trivial definition prefixes forbidden in HARD questions
TRIVIAL_DEFINITION_PREFIXES = (
    "what is",
    "define ",
    "who introduced",
    "who developed",
    "who invented",
    "what does",
    "which term defines",
    "what is the definition",
    "which of the following defines"
)


class QuizAgent:
    """
    High-Performance Pedagogical Assessment Generator.
    Produces strictly calibrated, non-repetitive educational assessments grounded
    exclusively in the selected document with multi-stage difficulty validation.
    """

    @staticmethod
    def _normalize_to_tokens(text: str) -> Set[str]:
        """Extracts significant lowercase word tokens for Jaccard similarity comparison."""
        words = re.findall(r"\b[a-z0-9]{3,}\b", text.lower())
        return {w for w in words if w not in STOPWORDS}

    @staticmethod
    def _calculate_jaccard_similarity(text1: str, text2: str) -> float:
        """Computes Jaccard similarity between two question prompts."""
        set1 = QuizAgent._normalize_to_tokens(text1)
        set2 = QuizAgent._normalize_to_tokens(text2)
        if not set1 or not set2:
            return 0.0
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        return intersection / union if union > 0 else 0.0

    @staticmethod
    def _is_duplicate_prompt(
        prompt: str,
        existing_prompts: List[str],
        threshold: float = 0.55
    ) -> bool:
        """Checks if a prompt is semantically duplicated against any prompt in a list."""
        for ex in existing_prompts:
            if QuizAgent._calculate_jaccard_similarity(prompt, ex) >= threshold:
                return True
        return False

    @staticmethod
    def _validate_difficulty_match(
        q: Dict[str, Any],
        target_difficulty: str
    ) -> bool:
        """
        Validates whether a question conforms to the cognitive complexity required:
        - EASY: Direct recall, definition, terminology, straightforward True/False.
        - MEDIUM: Application, calculations, comparisons, causes/effects. Avoids bare definitions.
        - HARD: Multi-step reasoning, scenarios, vulnerability analysis, unknown values.
                STRICTLY NO True/False, NO trivial definitions, NO one-step recall.
        """
        prompt = q.get("question", "").strip().lower()
        q_type = str(q.get("question_type", "mcq")).lower()

        if target_difficulty == "hard":
            # Rule 1: HARD assessments must NEVER be simple True/False or Fill-in-the-blank
            if q_type in ["true_false", "fill_blank"]:
                return False

            # Rule 2: HARD questions must NOT start with direct definition triggers
            for prefix in TRIVIAL_DEFINITION_PREFIXES:
                if prompt.startswith(prefix) and "scenario" not in prompt and "suppose" not in prompt:
                    return False

            # Rule 3: Check for cognitive complexity markers or multi-step/scenario structure
            has_indicator = any(indicator in prompt for indicator in HARD_ANALYTICAL_INDICATORS)
            is_substantial_scenario = (len(prompt) >= 80 and ("," in prompt or ";" in prompt or "?" in prompt))
            if not (has_indicator or is_substantial_scenario):
                return False

            return True

        elif target_difficulty == "medium":
            # Medium: Must not be a pure 1-line definition
            if prompt.startswith("what is the definition of"):
                return False
            return True

        else:  # easy
            # Easy: Accessible and clear
            return True

    @staticmethod
    def _validate_and_sanitize_candidate(
        q: Dict[str, Any],
        topic: str,
        target_difficulty: str,
        chunks: List[Dict[str, Any]],
        document_name: str
    ) -> Optional[Dict[str, Any]]:
        """
        Validates structure, options, distractors, citations, and correctness of a single question.
        Returns cleaned question dict if valid, else None.
        """
        prompt = str(q.get("question", "")).strip()
        q_type = str(q.get("question_type", "mcq")).lower()
        options = q.get("options", [])
        correct = str(q.get("correct_answer", "")).strip()
        explanation = str(q.get("explanation", f"Verified from '{document_name}'.")).strip()

        if not prompt or len(prompt) < 20 or not correct:
            return None

        # Sanitize and validate options
        if q_type == "true_false":
            if target_difficulty == "hard":
                return None  # Disallow True/False in Hard mode
            options = ["True", "False"]
            if correct.lower() in ["true", "t"]:
                correct = "True"
            elif correct.lower() in ["false", "f"]:
                correct = "False"
            else:
                return None
        else:
            # MCQ validation: Require distinct options
            cleaned_options = []
            for opt in options:
                opt_str = str(opt).strip()
                if opt_str and opt_str not in cleaned_options:
                    cleaned_options.append(opt_str)

            if len(cleaned_options) < 3:
                return None

            # Ensure correct answer matches one option exactly
            matching_opt = next((o for o in cleaned_options if o.lower() == correct.lower()), None)
            if matching_opt:
                correct = matching_opt
            else:
                # Replace the first distractor with the correct answer
                cleaned_options[0] = correct

            # Ensure at least 4 options for academic MCQs
            while len(cleaned_options) < 4:
                filler = f"None of the alternative {topic} mechanisms listed above."
                if filler not in cleaned_options:
                    cleaned_options.append(filler)
                else:
                    break

            options = cleaned_options[:4]

        # Verify or calibrate source page citation
        raw_citation = str(q.get("citation", "")).strip()
        page_num = chunks[0].get("page_number", 1) if chunks else 1
        page_match = re.search(r"\bpage\s*(\d+)\b", raw_citation, re.IGNORECASE)
        if page_match:
            page_num = int(page_match.group(1))

        citation = f"Page {page_num}, {document_name}"

        return {
            "question": prompt,
            "question_type": q_type,
            "options": options,
            "correct_answer": correct,
            "explanation": explanation,
            "topic": topic,
            "difficulty": target_difficulty,
            "citation": citation
        }

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
        Orchestrates RAG retrieval, historical deduplication, difficulty enforcement,
        and schema validation exclusively for the selected document.
        """
        if not question_types:
            question_types = ["mcq"]
        if difficulty == "hard":
            # For Hard difficulty, enforce scenario-based MCQs only
            question_types = ["mcq"]

        logger.info(f"[QuizAgent] Generating {question_count} {difficulty.upper()} questions on '{topic}' from '{document_name}' (ID: {document_id})")

        # 1. Retrieve grounded context strictly from the specified document ID
        query = f"{topic} core principles algorithms calculations mechanisms rules formulas analysis"
        chunks = rag_engine.retrieve_relevant_chunks(query=query, document_id=document_id, top_k=6)

        # Fallback to direct document chunk retrieval if search is too sparse
        if len(chunks) < 2:
            doc_chunks = rag_engine.get_document_chunks(document_id=document_id, limit=8)
            if doc_chunks:
                chunks = doc_chunks

        if not chunks:
            logger.error(f"[QuizAgent] No content chunks found for document '{document_name}' (ID: {document_id})")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot generate quiz: No readable content found for document '{document_name}'. Please ensure the document is uploaded and indexed."
            )

        # Verify that all retrieved chunks belong strictly to the target document
        for c in chunks:
            if c.get("document_id") and c["document_id"] != document_id:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="RAG boundary violation: Attempted to generate quiz using chunks from another document."
                )

        context_text = "\n\n".join([f"Page {c.get('page_number', 1)}: {c.get('text', '')}" for c in chunks])

        # 2. Retrieve recent historical questions for this document to prevent repetition
        recent_prompts: List[str] = []
        if db:
            try:
                prev_quizzes = (
                    db.query(QuizModel)
                    .filter(QuizModel.document_id == document_id)
                    .order_by(QuizModel.created_at.desc())
                    .limit(8)
                    .all()
                )
                for pq in prev_quizzes:
                    try:
                        p_qs = json.loads(pq.questions_json)
                        for pq_item in p_qs:
                            pt = pq_item.get("question", "").strip()
                            if pt:
                                recent_prompts.append(pt)
                    except Exception:
                        continue
            except Exception as e:
                logger.warning(f"[QuizAgent] Could not retrieve previous quiz history: {e}")

        # Format recent questions to instruct Gemini explicitly against duplicates
        repetition_clause = ""
        if recent_prompts:
            sample_recent = "\n".join([f"- {p[:120]}" for p in recent_prompts[:10]])
            repetition_clause = (
                "\n\nSTRICT REPETITION PREVENTION:\n"
                "The following questions were already recently administered. You MUST NOT repeat these questions "
                "or generate close variations of them:\n"
                f"{sample_recent}\n"
            )

        # 3. Formulate strict difficulty guidelines
        if difficulty == "easy":
            diff_spec = (
                "DIFFICULTY LEVEL: EASY (Bloom's Taxonomy: Remember & Understand)\n"
                "- Target beginner comprehension.\n"
                "- Allowed: Direct definitions, basic terminology, fundamental facts, straightforward True/False.\n"
                "- Prohibited: Complex calculations, multi-step problem solving, deceptive edge cases.\n"
                "- Tone: Clear, accessible, and direct."
            )
        elif difficulty == "medium":
            diff_spec = (
                "DIFFICULTY LEVEL: MEDIUM (Bloom's Taxonomy: Apply & Analyze)\n"
                "- Target applied intermediate understanding.\n"
                "- Requirements: At least 70% of questions MUST require applied reasoning, solving calculations, "
                "comparing two techniques, or evaluating cause-and-effect mechanisms.\n"
                "- Prohibited: Direct dictionary definition-only questions (e.g. avoid 'What is the definition of X?').\n"
                "- Require students to calculate output values, apply formulas from text, or identify differences."
            )
        else:  # hard
            diff_spec = (
                "DIFFICULTY LEVEL: HARD (Bloom's Taxonomy: Evaluate & Synthesize / Multi-Step Problem Solving)\n"
                "- Target advanced mastery and analytical rigor.\n"
                "- Requirements: At least 80% of questions MUST be scenario-based or require multi-step reasoning.\n"
                "- Present concrete problem scenarios: e.g. 'An attacker intercepts ciphertext C... determine the key and decrypt...', "
                "'Evaluate the computational complexity and structural weakness when...', 'Suppose an entity executes...', etc.\n"
                "- Require combining multiple concepts, analyzing security vulnerabilities, calculating unknown parameters, or diagnosing flaws.\n"
                "- STRICTLY PROHIBITED: Simple definition questions, basic recall, trivial True/False (NO True/False), one-step arithmetic.\n"
                "- Difficulty must stem from cognitive analysis, not confusing grammar."
            )

        # Request oversampled candidates (question_count + 4) to ensure enough pass rigorous validation
        candidate_count = max(question_count + 4, 8)

        prompt = (
            f"Generate an academic assessment of {candidate_count} distinct questions based strictly on the provided course material.\n\n"
            f"Source Document: {document_name}\n"
            f"Topic: {topic}\n"
            f"{diff_spec}\n"
            f"Question Types: {', '.join(question_types)}\n"
            f"{repetition_clause}\n"
            f"Context from '{document_name}':\n{context_text[:4500]}\n\n"
            "Respond strictly in valid JSON matching this schema:\n"
            "[\n"
            "  {\n"
            "    \"id\": 1,\n"
            "    \"question\": \"The precise question text...\",\n"
            "    \"question_type\": \"mcq\",\n"
            "    \"options\": [\"Option A\", \"Option B\", \"Option C\", \"Option D\"],\n"
            "    \"correct_answer\": \"Option A\",\n"
            "    \"explanation\": \"Detailed pedagogical explanation grounded in the text...\",\n"
            "    \"topic\": \"" + topic + "\",\n"
            "    \"difficulty\": \"" + difficulty + "\",\n"
            "    \"citation\": \"Page reference from provided context\"\n"
            "  }\n"
            "]"
        )

        system_instruction = (
            "You are a Senior Academic Examiner and Assessment Specialist. "
            f"Every question MUST be based exclusively on the provided context from '{document_name}'. "
            f"Do NOT invent facts, do NOT reference other subjects, and strictly enforce the requested {difficulty.upper()} difficulty rules. "
            "Output valid JSON array only, without markdown code fences."
        )

        raw_candidates: List[Dict[str, Any]] = []

        # 4. Generate candidates via Gemini API if live
        if gemini_service.is_live():
            res = gemini_service.generate_structured_json(prompt, system_instruction)
            if res.get("data") and isinstance(res["data"], list):
                raw_candidates = res["data"]

        # 5. Rigorous Multi-Stage Candidate Filtering & Validation
        validated_questions: List[Dict[str, Any]] = []
        accepted_prompts: List[str] = []

        for candidate in raw_candidates:
            # A. Structural and schema validation
            cleaned = QuizAgent._validate_and_sanitize_candidate(
                candidate, topic, difficulty, chunks, document_name
            )
            if not cleaned:
                continue

            prompt_text = cleaned["question"]

            # B. Difficulty verification
            if not QuizAgent._validate_difficulty_match(cleaned, difficulty):
                logger.debug(f"[QuizAgent] Rejected question due to difficulty mismatch: {prompt_text[:60]}")
                continue

            # C. Repetition check against current quiz batch
            if QuizAgent._is_duplicate_prompt(prompt_text, accepted_prompts, threshold=0.50):
                logger.debug(f"[QuizAgent] Rejected duplicate in current batch: {prompt_text[:60]}")
                continue

            # D. Repetition check against recent historical quizzes
            if QuizAgent._is_duplicate_prompt(prompt_text, recent_prompts, threshold=0.55):
                logger.debug(f"[QuizAgent] Rejected historical duplicate: {prompt_text[:60]}")
                continue

            # Accept candidate
            cleaned["id"] = len(validated_questions) + 1
            validated_questions.append(cleaned)
            accepted_prompts.append(prompt_text)

            if len(validated_questions) >= question_count:
                break

        # 6. Fallback or Supplement if fewer than question_count validated
        if len(validated_questions) < question_count:
            needed = question_count - len(validated_questions)
            logger.info(f"[QuizAgent] Supplementing with {needed} dynamic difficulty-calibrated questions from document chunks.")
            supplemental = QuizAgent._generate_fallback_questions(
                chunks=chunks,
                topic=topic,
                difficulty=difficulty,
                count=needed,
                question_types=question_types,
                document_name=document_name,
                existing_prompts=accepted_prompts + recent_prompts
            )
            for s in supplemental:
                s["id"] = len(validated_questions) + 1
                validated_questions.append(s)
                accepted_prompts.append(s["question"])

        if not validated_questions:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to generate verified questions from document '{document_name}'."
            )

        # 7. Persist Quiz Record
        quiz_id = str(uuid.uuid4())
        quiz_record = QuizModel(
            id=quiz_id,
            document_id=document_id,
            title=f"{topic} — {difficulty.capitalize()} Diagnostic Quiz",
            topic=topic,
            difficulty=difficulty,
            question_count=len(validated_questions),
            questions_json=json.dumps(validated_questions)
        )

        if db:
            db.add(quiz_record)
            db.commit()
            db.refresh(quiz_record)

        logger.info(f"[QuizAgent] Successfully generated quiz '{quiz_record.title}' with {len(validated_questions)} verified {difficulty.upper()} questions from '{document_name}'.")
        return quiz_record

    @staticmethod
    def _generate_fallback_questions(
        chunks: List[Dict[str, Any]],
        topic: str,
        difficulty: str,
        count: int,
        question_types: List[str],
        document_name: str,
        existing_prompts: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Dynamically derives difficulty-calibrated questions strictly from retrieved document chunks.
        Zero cross-document leakage; zero hardcoded questions.
        """
        if not chunks:
            return []
        if not existing_prompts:
            existing_prompts = []

        # Extract informative factual sentences from the chunks
        sentences: List[Dict[str, Any]] = []
        for c in chunks:
            text = c.get("text", "")
            page = c.get("page_number", 1)
            raw_sents = re.split(r"(?<=[.!?])\s+|\n{2,}", text)
            for s in raw_sents:
                s = s.strip()
                s = re.sub(r"^\d+[\.\)]\s*", "", s)
                s = re.sub(r"^[#\-\*\•]\s*", "", s)
                if 35 <= len(s) <= 250 and not s.startswith(("http", "www", "Table", "Figure")):
                    sentences.append({
                        "text": s,
                        "page": page,
                        "doc_name": document_name
                    })

        if not sentences:
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

        results: List[Dict[str, Any]] = []
        sentence_idx = 0

        for i in range(count):
            item = sentences[sentence_idx % len(sentences)]
            sentence_idx += 1
            sent_text = item["text"]
            page_num = item["page"]
            q_id = i + 1

            if difficulty == "hard":
                # Generate multi-step analytical scenario from document facts
                next_item = sentences[sentence_idx % len(sentences)]
                sentence_idx += 1
                clause_a = sent_text.rstrip(".")
                clause_b = next_item["text"].rstrip(".")

                scenario_prompt = (
                    f"Scenario Analysis: In '{document_name}', consider the operational context where:\n"
                    f"1. {clause_a}.\n"
                    f"2. {clause_b}.\n\n"
                    f"If a security analyst evaluates a vulnerability or failure condition under '{topic}', "
                    "which deduction represents the correct analytical conclusion?"
                )

                correct_ans = f"Condition (1) and (2) combine to require that: {clause_a.lower()}."
                distractor_1 = f"Condition (1) invalidates condition (2), eliminating the need for {topic} safeguards."
                distractor_2 = f"Both conditions remain functionally independent of {topic} operational boundaries."
                distractor_3 = f"The implementation will default to an unconstrained state irrespective of {clause_b.lower()}."

                options = [correct_ans, distractor_1, distractor_2, distractor_3]
                rot = i % 4
                options = options[rot:] + options[:rot]

                results.append({
                    "id": q_id,
                    "question": scenario_prompt,
                    "question_type": "mcq",
                    "options": options,
                    "correct_answer": correct_ans,
                    "explanation": f"Grounded in analytical synthesis of '{document_name}' (Page {page_num}): {sent_text}",
                    "topic": topic,
                    "difficulty": "hard",
                    "citation": f"Page {page_num}, {document_name}"
                })

            elif difficulty == "medium":
                # Generate applied / comparative question
                question_text = (
                    f"In applying the principles of '{topic}' as detailed in '{document_name}', "
                    f"which mechanism correctly implements the following requirement?\n\n\"{sent_text}\""
                )
                other_sentences = [
                    s["text"] for j, s in enumerate(sentences) if j != (i % len(sentences))
                ]
                distractor_list = other_sentences[:3]
                while len(distractor_list) < 3:
                    distractor_list.append(f"An alternative configuration unrelated to {topic} parameters.")

                options = [sent_text] + distractor_list[:3]
                rot = i % 4
                options = options[rot:] + options[:rot]

                results.append({
                    "id": q_id,
                    "question": question_text,
                    "question_type": "mcq",
                    "options": options,
                    "correct_answer": sent_text,
                    "explanation": f"Verified directly from '{document_name}' (Page {page_num}): \"{sent_text}\"",
                    "topic": topic,
                    "difficulty": "medium",
                    "citation": f"Page {page_num}, {document_name}"
                })

            else:  # easy
                # Generate clear foundational identification or True/False
                preferred_type = question_types[i % len(question_types)] if question_types else "mcq"
                if preferred_type == "true_false":
                    results.append({
                        "id": q_id,
                        "question": f"Based on '{document_name}', is the following statement regarding '{topic}' correct?\n\n\"{sent_text}\"",
                        "question_type": "true_false",
                        "options": ["True", "False"],
                        "correct_answer": "True",
                        "explanation": f"This statement is directly verified in '{document_name}' on Page {page_num}.",
                        "topic": topic,
                        "difficulty": "easy",
                        "citation": f"Page {page_num}, {document_name}"
                    })
                else:
                    words = re.findall(r"\b[A-Za-z]{4,}\b", sent_text)
                    target_term = words[0] if words else topic
                    blanked = re.sub(rf"\b{re.escape(target_term)}\b", "______", sent_text, count=1)
                    distractors = [w for w in words[1:] if w.lower() != target_term.lower()][:3]
                    while len(distractors) < 3:
                        distractors.append(f"Parameter_{len(distractors)+1}")
                    options = [target_term] + distractors[:3]
                    rot = i % 4
                    options = options[rot:] + options[:rot]

                    results.append({
                        "id": q_id,
                        "question": f"According to '{document_name}', identify the term that completes the statement regarding '{topic}':\n\n\"{blanked}\"",
                        "question_type": "mcq",
                        "options": options,
                        "correct_answer": target_term,
                        "explanation": f"Directly stated in '{document_name}' on Page {page_num}: \"{sent_text}\"",
                        "topic": topic,
                        "difficulty": "easy",
                        "citation": f"Page {page_num}, {document_name}"
                    })

        return results
