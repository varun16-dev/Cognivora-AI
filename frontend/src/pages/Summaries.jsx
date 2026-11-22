import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  FileText,
  Sparkles,
  Volume2,
  Copy,
  Check,
  BookOpen,
  ArrowRight,
  ListOrdered,
  Lightbulb,
  Zap,
  BookmarkCheck,
  RefreshCw,
  AlertCircle
} from 'lucide-react';
import { api } from '../services/api';

const summaryModes = [
  { id: 'short', name: '⚡ Short (2 Min)', desc: 'Executive high-impact overview' },
  { id: 'detailed', name: '📖 Detailed', desc: 'Thorough textbook chapter breakdown' },
  { id: 'key_points', name: '🎯 Key Takeaways', desc: 'Bulleted checklist of crucial rules' },
  { id: 'beginner', name: '💡 Beginner-Friendly', desc: 'Real-world intuitive analogies' },
  { id: 'exam_notes', name: '📝 Exam Cram', desc: 'Formulas, definitions, and pitfalls' },
];

export default function Summaries() {
  const navigate = useNavigate();
  const [documents, setDocuments] = useState([]);
  const [selectedDocId, setSelectedDocId] = useState('');
  const [topic, setTopic] = useState('Operating Systems Deadlocks');
  const [mode, setMode] = useState('detailed');
  const [summaries, setSummaries] = useState([]);
  const [activeSummary, setActiveSummary] = useState(null);
  const [loading, setLoading] = useState(false);
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    api.getDocuments()
      .then((docs) => {
        setDocuments(docs);
        if (docs.length > 0) {
          setSelectedDocId(docs[0].id);
          if (docs[0].topics && docs[0].topics.length > 0) setTopic(docs[0].topics[0]);
        }
      })
      .catch((err) => console.log('Error fetching docs for summaries:', err));

    api.getSummaries()
      .then((list) => {
        setSummaries(list);
        if (list.length > 0) setActiveSummary(list[0]);
      })
      .catch((err) => console.log('Error fetching summaries:', err));
  }, []);

  const handleGenerateSummary = async () => {
    if (!selectedDocId) {
      setError('Please select an uploaded document.');
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const newSummary = await api.generateSummary({
        document_id: selectedDocId,
        topic,
        mode
      });
      setSummaries((prev) => [newSummary, ...prev]);
      setActiveSummary(newSummary);
    } catch (err) {
      setError(`Failed to generate summary: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleCopy = () => {
    if (!activeSummary) return;
    navigator.clipboard.writeText(activeSummary.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleSendToAudio = () => {
    if (!activeSummary) return;
    navigate('/audio', {
      state: {
        text: activeSummary.content,
        title: activeSummary.title
      }
    });
  };

  return (
    <div className="max-w-5xl mx-auto space-y-8">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-black text-slate-900 tracking-tight">
          AI Summary & Conceptual Digest Generator
        </h2>
        <p className="text-sm text-slate-500 mt-1">
          Synthesize academic notes into executive summaries, high-yield exam sheets, or beginner analogies.
          Listen to any summary with one click in the Audio Learning Lab.
        </p>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-red-50 border border-red-200 text-red-700 text-sm flex items-center gap-2">
          <AlertCircle className="w-5 h-5 shrink-0 text-red-600" />
          <span>{error}</span>
        </div>
      )}

      {/* Generator Configuration Card */}
      <div className="bg-white rounded-2xl p-6 border border-slate-200/80 shadow-xs space-y-5">
        <h3 className="font-bold text-base text-slate-900 flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-violet-600" />
          <span>Configure Summary Style & Target</span>
        </h3>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-bold text-slate-600 mb-1">Source Document</label>
            <select
              value={selectedDocId}
              onChange={(e) => {
                setSelectedDocId(e.target.value);
                const doc = documents.find((d) => d.id === e.target.value);
                if (doc && doc.topics?.length > 0) setTopic(doc.topics[0]);
              }}
              className="w-full bg-slate-50 border border-slate-300 rounded-xl px-3 py-2 text-xs text-slate-800"
            >
              {documents.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.filename}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-600 mb-1">Topic / Chapter</label>
            <input
              type="text"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              className="w-full bg-slate-50 border border-slate-300 rounded-xl px-3 py-2 text-xs text-slate-800"
            />
          </div>
        </div>

        {/* Mode Selector */}
        <div>
          <label className="block text-xs font-bold text-slate-600 mb-2">Pedagogical Mode</label>
          <div className="grid grid-cols-2 sm:grid-cols-5 gap-2">
            {summaryModes.map((m) => (
              <button
                key={m.id}
                type="button"
                onClick={() => setMode(m.id)}
                className={`p-3 rounded-xl text-left border transition ${
                  mode === m.id
                    ? 'border-violet-600 bg-violet-50 text-violet-900 shadow-xs'
                    : 'border-slate-200 bg-slate-50 text-slate-600 hover:bg-slate-100'
                }`}
              >
                <p className="font-bold text-xs">{m.name}</p>
                <p className="text-[10px] text-slate-500 mt-1 line-clamp-2">{m.desc}</p>
              </button>
            ))}
          </div>
        </div>

        <div className="pt-2 flex justify-end">
          <button
            onClick={handleGenerateSummary}
            disabled={loading || !selectedDocId}
            className="px-6 py-2.5 rounded-xl bg-violet-600 hover:bg-violet-700 disabled:opacity-50 text-white font-bold text-xs transition flex items-center gap-2 shadow-xs"
          >
            {loading ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin" />
                <span>SummaryAgent Synthesizing...</span>
              </>
            ) : (
              <>
                <span>Generate Summary</span>
                <ArrowRight className="w-4 h-4" />
              </>
            )}
          </button>
        </div>
      </div>

      {/* Summary Viewer with Spoken Lesson Trigger */}
      {activeSummary && (
        <div className="bg-white rounded-2xl border border-slate-200/80 shadow-xs overflow-hidden">
          {/* Viewer Toolbar */}
          <div className="p-5 border-b border-slate-100 flex flex-wrap items-center justify-between gap-4 bg-slate-50/50">
            <div>
              <span className="text-[11px] font-bold text-violet-700 uppercase tracking-wider px-2.5 py-0.5 rounded-full bg-violet-50 border border-violet-100">
                {activeSummary.mode.replace('_', ' ').toUpperCase()} • {activeSummary.topic}
              </span>
              <h3 className="font-bold text-lg text-slate-900 mt-1">
                {activeSummary.title}
              </h3>
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={handleCopy}
                className="px-3 py-1.5 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 text-xs font-semibold text-slate-700 transition flex items-center gap-1.5"
              >
                {copied ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
                <span>{copied ? 'Copied' : 'Copy'}</span>
              </button>

              <button
                onClick={handleSendToAudio}
                className="px-4 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold transition flex items-center gap-1.5 shadow-xs"
              >
                <Volume2 className="w-3.5 h-3.5" />
                <span>Listen Spoken Lesson</span>
              </button>
            </div>
          </div>

          {/* Formatted Markdown Content */}
          <div className="p-6 sm:p-8 space-y-6">
            <div className="prose prose-slate max-w-none text-sm sm:text-base text-slate-800 leading-relaxed whitespace-pre-wrap">
              {activeSummary.content}
            </div>

            {/* Key Points Checklist */}
            {activeSummary.key_points && activeSummary.key_points.length > 0 && (
              <div className="p-5 rounded-xl bg-slate-50 border border-slate-200/80 space-y-3">
                <h4 className="font-bold text-xs uppercase tracking-wider text-slate-600 flex items-center gap-1.5">
                  <BookmarkCheck className="w-4 h-4 text-violet-600" />
                  <span>Key Conceptual Takeaways Checklist</span>
                </h4>
                <ul className="space-y-2 text-xs sm:text-sm text-slate-700">
                  {activeSummary.key_points.map((pt, idx) => (
                    <li key={idx} className="flex items-start gap-2">
                      <span className="text-violet-600 font-bold shrink-0 mt-0.5">•</span>
                      <span>{pt}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
