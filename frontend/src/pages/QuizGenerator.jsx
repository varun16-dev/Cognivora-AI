import React, { useState, useEffect } from 'react';
import {
  Award,
  Sparkles,
  CheckCircle2,
  XCircle,
  HelpCircle,
  Clock,
  ArrowRight,
  ArrowLeft,
  RotateCcw,
  BookOpen,
  AlertTriangle,
  Send,
  RefreshCw,
  Download
} from 'lucide-react';
import { api } from '../services/api';

export default function QuizGenerator() {
  const [documents, setDocuments] = useState([]);
  const [selectedDocId, setSelectedDocId] = useState('');
  const [topic, setTopic] = useState('');
  const [difficulty, setDifficulty] = useState('medium');
  const [questionCount, setQuestionCount] = useState(5);
  const [questionTypes, setQuestionTypes] = useState(['mcq', 'true_false']);

  // Flow states: 'config' | 'taking' | 'result'
  const [quizState, setQuizState] = useState('config');
  const [activeQuiz, setActiveQuiz] = useState(null);
  const [userAnswers, setUserAnswers] = useState({});
  const [currentQIndex, setCurrentQIndex] = useState(0);
  const [quizResult, setQuizResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    api.getDocuments()
      .then((docs) => {
        setDocuments(docs);
        if (docs.length > 0) {
          const firstDoc = docs[0];
          setSelectedDocId(firstDoc.id);
          const initialTopic = (firstDoc.topics && firstDoc.topics.length > 0 && firstDoc.topics[0] !== 'General')
            ? firstDoc.topics[0]
            : (firstDoc.subject || 'Core Concepts');
          setTopic(initialTopic);
        }
      })
      .catch((err) => console.log('Could not load documents for quiz:', err));
  }, []);

  const handleDocumentChange = (docId) => {
    setSelectedDocId(docId);
    setActiveQuiz(null);
    setQuizResult(null);
    setUserAnswers({});
    setCurrentQIndex(0);
    setError(null);
    setQuizState('config');
    const doc = documents.find((d) => d.id === docId);
    if (doc) {
      const docTopic = (doc.topics && doc.topics.length > 0 && doc.topics[0] !== 'General')
        ? doc.topics[0]
        : (doc.subject || 'Core Concepts');
      setTopic(docTopic);
    }
  };

  const handleTopicChange = (newTopic) => {
    setTopic(newTopic);
    setActiveQuiz(null);
    setQuizResult(null);
    setUserAnswers({});
    setCurrentQIndex(0);
    setError(null);
  };

  const handleNewQuiz = () => {
    setActiveQuiz(null);
    setQuizResult(null);
    setUserAnswers({});
    setCurrentQIndex(0);
    setError(null);
    setQuizState('config');
  };

  const currentDoc = documents.find((d) => d.id === selectedDocId);

  const handleGenerateQuiz = async () => {
    if (!selectedDocId) {
      setError('Please upload or select an academic document first.');
      return;
    }

    setLoading(true);
    setError(null);

    const doc = documents.find((d) => d.id === selectedDocId);
    const resolvedTopic = topic.trim() || (doc ? (doc.subject || 'Core Concepts') : 'Core Concepts');

    try {
      const res = await api.generateQuiz({
        document_id: selectedDocId,
        topic: resolvedTopic,
        difficulty,
        question_count: Number(questionCount),
        question_types: questionTypes
      });

      setActiveQuiz(res);
      setUserAnswers({});
      setCurrentQIndex(0);
      setQuizState('taking');
    } catch (err) {
      console.error('Quiz generation error:', err);
      setError(`Failed to generate quiz: ${err.message || 'Check backend service'}`);
    } finally {
      setLoading(false);
    }
  };

  const handleSelectOption = (qId, option) => {
    setUserAnswers((prev) => ({
      ...prev,
      [qId]: option
    }));
  };

  const handleSubmitQuiz = async () => {
    if (!activeQuiz) return;
    setLoading(true);
    setError(null);

    const answersPayload = activeQuiz.questions.map((q) => ({
      question_id: q.id,
      selected_answer: userAnswers[q.id] || ''
    }));

    try {
      const result = await api.submitQuiz({
        quiz_id: activeQuiz.id,
        answers: answersPayload
      });
      setQuizResult(result);
      setQuizState('result');
    } catch (err) {
      console.error('Submission error:', err);
      setError(`Failed to evaluate quiz: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleRetake = () => {
    setUserAnswers({});
    setCurrentQIndex(0);
    setQuizResult(null);
    setQuizState('taking');
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      {/* Page Title */}
      <div>
        <h2 className="text-2xl font-black text-slate-900 tracking-tight">
          AI Quiz Generator & Assessment Station
        </h2>
        <p className="text-sm text-slate-500 mt-1">
          Generate calibrated, multi-type educational assessments grounded in your course materials.
          Every question includes answer verification, pedagogical explanations, and exact citations.
        </p>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-red-50 border border-red-200 text-red-700 text-sm flex items-center gap-2">
          <AlertTriangle className="w-5 h-5 shrink-0 text-red-600" />
          <span>{error}</span>
        </div>
      )}

      {/* STEP 1: Quiz Configuration Form */}
      {quizState === 'config' && (
        <div className="bg-white rounded-2xl p-6 sm:p-8 border border-slate-200/80 shadow-xs space-y-6">
          <h3 className="font-bold text-lg text-slate-900 flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-violet-600" />
            <span>Configure Assessment Parameters</span>
          </h3>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
            {/* Document Select */}
            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
                Source Document
              </label>
              <select
                value={selectedDocId}
                onChange={(e) => handleDocumentChange(e.target.value)}
                className="w-full bg-slate-50 border border-slate-300 rounded-xl px-4 py-2.5 text-sm text-slate-800 font-medium focus:ring-2 focus:ring-violet-500 focus:outline-hidden"
              >
                {documents.length === 0 && <option value="">No documents uploaded yet</option>}
                {documents.map((d) => (
                  <option key={d.id} value={d.id}>
                    {d.filename} ({d.subject})
                  </option>
                ))}
              </select>
            </div>

            {/* Topic Input */}
            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
                Curriculum Topic
              </label>
              <input
                type="text"
                value={topic}
                onChange={(e) => handleTopicChange(e.target.value)}
                placeholder={currentDoc ? `e.g. ${currentDoc.subject || 'Core Concepts'}` : "e.g. Classical Encryption, Substitution Ciphers"}
                className="w-full bg-slate-50 border border-slate-300 rounded-xl px-4 py-2.5 text-sm text-slate-800 font-medium focus:ring-2 focus:ring-violet-500 focus:outline-hidden"
              />
              {currentDoc && currentDoc.topics && currentDoc.topics.length > 0 && (
                <div className="mt-2.5 flex flex-wrap gap-1.5 items-center">
                  <span className="text-[11px] font-semibold text-slate-500">Document Topics:</span>
                  {currentDoc.topics.slice(0, 5).map((t, idx) => (
                    <button
                      key={idx}
                      type="button"
                      onClick={() => handleTopicChange(t)}
                      className={`text-[11px] px-2 py-0.5 rounded-md border transition ${
                        topic === t
                          ? 'bg-violet-100 text-violet-800 border-violet-300 font-semibold'
                          : 'bg-slate-100 text-slate-600 border-slate-200 hover:bg-slate-200'
                      }`}
                    >
                      {t}
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* Difficulty Selector */}
            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
                Difficulty Level
              </label>
              <div className="grid grid-cols-3 gap-2">
                {['easy', 'medium', 'hard'].map((lvl) => (
                  <button
                    key={lvl}
                    type="button"
                    onClick={() => setDifficulty(lvl)}
                    className={`py-2 rounded-xl text-xs font-bold uppercase transition ${
                      difficulty === lvl
                        ? 'bg-violet-600 text-white shadow-xs'
                        : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                    }`}
                  >
                    {lvl}
                  </button>
                ))}
              </div>
            </div>

            {/* Question Count */}
            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
                Question Count
              </label>
              <div className="grid grid-cols-3 gap-2">
                {[3, 5, 10].map((num) => (
                  <button
                    key={num}
                    type="button"
                    onClick={() => setQuestionCount(num)}
                    className={`py-2 rounded-xl text-xs font-bold transition ${
                      questionCount === num
                        ? 'bg-violet-600 text-white shadow-xs'
                        : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                    }`}
                  >
                    {num} Questions
                  </button>
                ))}
              </div>
            </div>
          </div>

          <div className="pt-4 border-t border-slate-100 flex justify-end">
            <button
              onClick={handleGenerateQuiz}
              disabled={loading || !selectedDocId}
              className="px-6 py-3 rounded-xl bg-violet-600 hover:bg-violet-500 disabled:opacity-50 text-white font-bold text-sm transition shadow-lg shadow-violet-600/30 flex items-center gap-2"
            >
              {loading ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  <span>QuizAgent Generating Questions...</span>
                </>
              ) : (
                <>
                  <span>Generate Diagnostic Quiz</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </div>
        </div>
      )}

      {/* STEP 2: Interactive Quiz Runner */}
      {quizState === 'taking' && activeQuiz && (
        <div className="bg-white rounded-2xl p-6 sm:p-8 border border-slate-200/80 shadow-xs space-y-6">
          {/* Quiz Header & Progress */}
          <div className="flex items-center justify-between pb-4 border-b border-slate-100">
            <div>
              <span className="text-[11px] font-bold text-violet-600 uppercase tracking-wider px-2.5 py-0.5 rounded-full bg-violet-50 border border-violet-100">
                {activeQuiz.difficulty.toUpperCase()} • {activeQuiz.topic}
              </span>
              <h3 className="font-bold text-base text-slate-900 mt-1">
                {activeQuiz.title}
              </h3>
            </div>
            <div className="text-right">
              <span className="text-xs font-bold text-slate-400">
                Question {currentQIndex + 1} of {activeQuiz.questions.length}
              </span>
            </div>
          </div>

          {/* Progress Bar */}
          <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden">
            <div
              className="bg-violet-600 h-full transition-all duration-300"
              style={{
                width: `${((currentQIndex + 1) / activeQuiz.questions.length) * 100}%`
              }}
            ></div>
          </div>

          {/* Active Question Box */}
          {activeQuiz.questions[currentQIndex] && (
            <div className="space-y-6 py-2">
              <div className="flex items-start gap-3">
                <span className="w-7 h-7 rounded-lg bg-violet-600 text-white font-bold text-xs flex items-center justify-center shrink-0 mt-0.5">
                  Q{currentQIndex + 1}
                </span>
                <p className="text-base font-semibold text-slate-900 leading-snug">
                  {activeQuiz.questions[currentQIndex].question}
                </p>
              </div>

              {/* Options List */}
              <div className="space-y-3 pl-10">
                {activeQuiz.questions[currentQIndex].options.map((opt, oIdx) => {
                  const currentQId = activeQuiz.questions[currentQIndex].id;
                  const isSelected = userAnswers[currentQId] === opt;
                  return (
                    <button
                      key={oIdx}
                      type="button"
                      onClick={() => handleSelectOption(currentQId, opt)}
                      className={`w-full text-left p-4 rounded-xl border text-sm font-medium transition flex items-center justify-between ${
                        isSelected
                          ? 'border-violet-600 bg-violet-50/80 text-violet-900 shadow-xs'
                          : 'border-slate-200 hover:border-slate-300 bg-white text-slate-700 hover:bg-slate-50'
                      }`}
                    >
                      <span>{opt}</span>
                      <div
                        className={`w-5 h-5 rounded-full border flex items-center justify-center ${
                          isSelected ? 'border-violet-600 bg-violet-600 text-white' : 'border-slate-300'
                        }`}
                      >
                        {isSelected && <span className="w-2 h-2 rounded-full bg-white"></span>}
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>
          )}

          {/* Runner Navigation Footer */}
          <div className="pt-4 border-t border-slate-100 flex items-center justify-between">
            <button
              onClick={() => setCurrentQIndex((prev) => Math.max(0, prev - 1))}
              disabled={currentQIndex === 0}
              className="px-4 py-2 rounded-xl border border-slate-200 text-xs font-semibold text-slate-600 hover:bg-slate-50 disabled:opacity-40 transition flex items-center gap-1.5"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              <span>Previous</span>
            </button>

            {currentQIndex < activeQuiz.questions.length - 1 ? (
              <button
                onClick={() => setCurrentQIndex((prev) => prev + 1)}
                className="px-5 py-2.5 rounded-xl bg-violet-600 hover:bg-violet-700 text-white text-xs font-bold transition flex items-center gap-1.5"
              >
                <span>Next Question</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            ) : (
              <button
                onClick={handleSubmitQuiz}
                disabled={loading}
                className="px-6 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold transition flex items-center gap-2 shadow-xs"
              >
                {loading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <CheckCircle2 className="w-4 h-4" />}
                <span>Submit & Grade Quiz</span>
              </button>
            )}
          </div>
        </div>
      )}

      {/* STEP 3: Detailed Score & Review Breakdown */}
      {quizState === 'result' && quizResult && (
        <div className="space-y-6">
          {/* Big Score Banner */}
          <div
            className={`rounded-2xl p-6 sm:p-8 text-white shadow-xl ${
              quizResult.percentage >= 80
                ? 'bg-gradient-to-r from-emerald-600 to-teal-700'
                : quizResult.percentage >= 60
                ? 'bg-gradient-to-r from-amber-600 to-orange-700'
                : 'bg-gradient-to-r from-red-600 to-rose-700'
            }`}
          >
            <div className="flex flex-col sm:flex-row items-center justify-between gap-6">
              <div>
                <span className="text-xs uppercase font-bold tracking-wider px-3 py-1 rounded-full bg-white/20">
                  Assessment Completed
                </span>
                <h3 className="text-3xl font-black mt-2">
                  Score: {quizResult.percentage}% ({quizResult.score} of {quizResult.total_questions} Correct)
                </h3>
                <p className="text-white/90 text-sm mt-1 max-w-xl">
                  {quizResult.feedback}
                </p>
              </div>

              <div className="flex flex-wrap items-center gap-3">
                <a
                  href={api.exportQuizUrl(quizResult.quiz_id)}
                  download
                  className="px-4 py-2 rounded-xl bg-white/20 hover:bg-white/30 text-white font-bold text-xs transition shadow-xs flex items-center gap-1.5"
                >
                  <Download className="w-4 h-4" />
                  <span>Export Quiz Sheet</span>
                </a>
                <button
                  onClick={handleRetake}
                  className="px-4 py-2 rounded-xl bg-white text-slate-900 font-bold text-xs hover:bg-slate-100 transition shadow-xs flex items-center gap-1.5"
                >
                  <RotateCcw className="w-4 h-4" />
                  <span>Retake</span>
                </button>
                <button
                  onClick={handleNewQuiz}
                  className="px-4 py-2 rounded-xl bg-black/30 text-white font-bold text-xs hover:bg-black/40 transition"
                >
                  New Quiz
                </button>
              </div>
            </div>
          </div>

          {/* Question-by-Question Pedagogical Review */}
          <div className="bg-white rounded-2xl p-6 sm:p-8 border border-slate-200/80 shadow-xs space-y-6">
            <h4 className="font-bold text-base text-slate-900">
              Detailed Question Review & Explanations
            </h4>

            <div className="space-y-5">
              {quizResult.evaluations.map((ev, idx) => (
                <div
                  key={idx}
                  className={`p-5 rounded-xl border text-sm space-y-3 ${
                    ev.is_correct
                      ? 'border-emerald-200 bg-emerald-50/30'
                      : 'border-red-200 bg-red-50/30'
                  }`}
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex items-start gap-2.5">
                      {ev.is_correct ? (
                        <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0 mt-0.5" />
                      ) : (
                        <XCircle className="w-5 h-5 text-red-600 shrink-0 mt-0.5" />
                      )}
                      <p className="font-bold text-slate-900">
                        {idx + 1}. {ev.question}
                      </p>
                    </div>
                    <span
                      className={`text-[11px] font-bold px-2 py-0.5 rounded-full uppercase ${
                        ev.is_correct
                          ? 'bg-emerald-100 text-emerald-800'
                          : 'bg-red-100 text-red-800'
                      }`}
                    >
                      {ev.is_correct ? 'Correct' : 'Incorrect'}
                    </span>
                  </div>

                  <div className="pl-7 space-y-1 text-xs">
                    <p className="text-slate-600">
                      Your answer: <span className="font-semibold">{ev.selected_answer || '(No answer provided)'}</span>
                    </p>
                    {!ev.is_correct && (
                      <p className="text-emerald-700 font-semibold">
                        Correct answer: <span>{ev.correct_answer}</span>
                      </p>
                    )}
                    <div className="mt-2 p-3 rounded-lg bg-white/80 border border-slate-200/70 text-slate-700">
                      <p className="font-semibold text-slate-900 mb-0.5">Pedagogical Explanation:</p>
                      <p>{ev.explanation}</p>
                      {ev.citation && (
                        <p className="text-[10px] text-slate-400 mt-1.5 italic">
                          Reference: {ev.citation}
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
