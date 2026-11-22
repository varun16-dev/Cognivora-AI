import json
from datetime import datetime
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.database.models import DocumentModel, QuizModel, QuizAttemptModel, FlashcardDeckModel, SummaryModel
from app.schemas.schemas import (
    AnalyticsDashboardResponse,
    TopicMasteryItem,
    QuizHistoryItem
)


class AnalyticsService:
    """
    Adaptive Learning Analytics Engine.
    Implements Exponentially Weighted Moving Average (EWMA) topic mastery tracking,
    diagnostic skill profiling, and personalized study recommendations.
    """

    @staticmethod
    def get_dashboard_metrics(db: Session) -> AnalyticsDashboardResponse:
        """
        Aggregates overall student performance, topic readiness heatmaps, and revision alerts.
        """
        total_docs = db.query(DocumentModel).count()
        attempts = db.query(QuizAttemptModel).order_by(QuizAttemptModel.completed_at.desc()).all()
        total_attempts = len(attempts)
        total_flashcards = db.query(FlashcardDeckModel).count()
        total_summaries = db.query(SummaryModel).count()

        # Compute average quiz score
        avg_score = 0.0
        if total_attempts > 0:
            avg_score = round(sum(a.percentage for a in attempts) / total_attempts, 1)

        # Topic-level aggregation
        topic_stats: Dict[str, Dict[str, Any]] = {}
        for a in attempts:
            topic = a.topic or "General"
            if topic not in topic_stats:
                topic_stats[topic] = {
                    "total_questions": 0,
                    "correct_count": 0,
                    "scores": [],
                    "subject": "General Studies"
                }
            topic_stats[topic]["total_questions"] += a.total_questions
            topic_stats[topic]["correct_count"] += a.score
            topic_stats[topic]["scores"].append(a.percentage)

        # If no attempts yet, populate default syllabus baseline so dashboard is never empty
        if not topic_stats:
            default_topics = [
                ("The Deadlock Problem & 4 Conditions", 85.0, 10, 8),
                ("Banker's Algorithm & Safe Sequences", 55.0, 10, 5),
                ("Deadlock Prevention vs. Avoidance", 70.0, 10, 7),
                ("Resource Allocation Graphs (RAG)", 50.0, 10, 5),
            ]
            for t_name, score, t_q, c_q in default_topics:
                topic_stats[t_name] = {
                    "total_questions": t_q,
                    "correct_count": c_q,
                    "scores": [score],
                    "subject": "Operating Systems"
                }

        topic_mastery: List[TopicMasteryItem] = []
        weak_topics: List[str] = []
        recommendations: List[str] = []

        alpha = 0.35  # EWMA learning rate weighting recent performance
        for topic_name, stat in topic_stats.items():
            scores = stat["scores"]
            # Calculate EWMA
            ewma = scores[0]
            for s in scores[1:]:
                ewma = (alpha * s) + ((1.0 - alpha) * ewma)
            mastery_pct = round(ewma, 1)

            if mastery_pct >= 80.0:
                status = "mastered"
                action = "Mastered. Review periodically to maintain retention."
            elif mastery_pct >= 60.0:
                status = "developing"
                action = "Developing comprehension. Take a medium-difficulty practice quiz."
            else:
                status = "weak"
                action = "Critical deficit (<60%). Review high-yield notes and attempt an easy diagnostic quiz."
                weak_topics.append(topic_name)
                recommendations.append(f"Focus revision on '{topic_name}': Practice 5 targeted questions or listen to an audio lesson.")

            topic_mastery.append(TopicMasteryItem(
                topic=topic_name,
                subject=stat.get("subject", "Computer Science"),
                mastery_percentage=mastery_pct,
                status=status,
                total_questions=stat["total_questions"],
                correct_count=stat["correct_count"],
                recommended_action=action
            ))

        if not recommendations:
            recommendations.append("All attempted topics are above 60% mastery! Advance to Hard difficulty quizzes.")

        # Recent quiz history list
        recent_history: List[QuizHistoryItem] = []
        for a in attempts[:10]:
            quiz = db.query(QuizModel).filter(QuizModel.id == a.quiz_id).first()
            title = quiz.title if quiz else "Course Assessment"
            recent_history.append(QuizHistoryItem(
                attempt_id=a.id,
                quiz_title=title,
                topic=a.topic,
                difficulty=a.difficulty,
                score=a.score,
                total=a.total_questions,
                percentage=a.percentage,
                completed_at=a.completed_at
            ))

        return AnalyticsDashboardResponse(
            total_documents=total_docs,
            total_quizzes_attempted=total_attempts,
            average_quiz_score=avg_score,
            total_flashcards_created=total_flashcards,
            total_summaries_generated=total_summaries,
            topic_mastery=sorted(topic_mastery, key=lambda x: x.mastery_percentage),
            recent_quiz_history=recent_history,
            weak_topics=weak_topics,
            improvement_recommendations=recommendations
        )
