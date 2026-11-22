import React, { useState, useEffect, useRef } from 'react';
import {
  Send,
  Bot,
  User,
  Sparkles,
  BookOpen,
  FileText,
  HelpCircle,
  Clock,
  Layers,
  ChevronDown,
  Info,
  RefreshCw,
  ExternalLink,
  ShieldCheck
} from 'lucide-react';
import { api } from '../services/api';

const pedagogicalModes = [
  { id: 'standard', name: 'Standard Academic', desc: 'Balanced pedagogical answers' },
  { id: 'explain_simply', name: '💡 Explain Simply', desc: 'Intuitive analogies, plain language' },
  { id: 'exam_cram', name: '⚡ Exam Cram', desc: 'Definitions, formulas, common pitfalls' },
  { id: 'deep_dive', name: '🔍 Deep Dive', desc: 'In-depth theoretical breakdown' },
];

const samplePrompts = [
  "What are the 4 necessary conditions for a deadlock?",
  "How does Dijkstra's Banker's Algorithm avoid deadlocks?",
  "Explain the difference between Deadlock Prevention and Avoidance",
  "Generate a 5-question practice quiz on Deadlocks"
];

export default function StudyChat() {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content:
        "Hello! I am your **Cognivora AI Study Assistant**. " +
        "I am strictly grounded in your uploaded curriculum documents to prevent hallucinations. " +
        "Ask me any question about your course materials, request a practice quiz, or select an explanation mode below!",
      citations: [],
      agent_decision: "System initialization. Ready to orchestrate specialized educational tools.",
      intent_detected: "greeting",
      model_used: "Gemini 2.5 Flash",
      is_demo_mode: false,
    }
  ]);
  const [input, setInput] = useState('');
  const [mode, setMode] = useState('standard');
  const [documents, setDocuments] = useState([]);
  const [selectedDocId, setSelectedDocId] = useState('');
  const [loading, setLoading] = useState(false);
  const [activeDecision, setActiveDecision] = useState(null);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    api.getDocuments()
      .then((docs) => {
        setDocuments(docs);
        if (docs.length > 0) {
          setSelectedDocId(docs[0].id);
        }
      })
      .catch((err) => console.log('Could not fetch docs for chat filter:', err));
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const handleSend = async (textToSend) => {
    const text = textToSend || input;
    if (!text.trim() || loading) return;

    const userMsg = {
      role: 'user',
      content: text,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    setMessages((prev) => [...prev, userMsg]);
    if (!textToSend) setInput('');
    setLoading(true);

    try {
      const res = await api.sendChatMessage({
        message: text,
        document_id: selectedDocId || null,
        pedagogical_mode: mode
      });

      const aiMsg = {
        role: 'assistant',
        content: res.answer,
        citations: res.citations || [],
        agent_decision: res.agent_decision,
        intent_detected: res.intent_detected,
        model_used: res.model_used,
        is_demo_mode: res.is_demo_mode,
        grounded_in_docs: res.grounded_in_docs,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };

      setMessages((prev) => [...prev, aiMsg]);
    } catch (err) {
      console.error('Chat error:', err);
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: `⚠️ Error contacting the Coordinator Agent: ${err.message || 'Check backend status'}`,
          citations: [],
          agent_decision: "Execution failure in chat pipeline.",
          model_used: "Fallback"
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-8rem)] max-w-5xl mx-auto bg-white rounded-2xl border border-slate-200/80 shadow-xs overflow-hidden">
      {/* Top Controls Bar */}
      <div className="p-4 bg-slate-50 border-b border-slate-200/80 flex flex-wrap items-center justify-between gap-3">
        {/* Pedagogical Mode Select */}
        <div className="flex items-center gap-2">
          <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">Mode:</span>
          <div className="flex bg-slate-200/70 p-0.5 rounded-lg">
            {pedagogicalModes.map((m) => (
              <button
                key={m.id}
                onClick={() => setMode(m.id)}
                className={`px-2.5 py-1 rounded-md text-xs font-semibold transition ${
                  mode === m.id
                    ? 'bg-white text-violet-700 shadow-xs'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
                title={m.desc}
              >
                {m.name}
              </button>
            ))}
          </div>
        </div>

        {/* Document Filter */}
        <div className="flex items-center gap-2 text-xs">
          <span className="font-bold text-slate-500 uppercase tracking-wider">Target:</span>
          <select
            value={selectedDocId}
            onChange={(e) => setSelectedDocId(e.target.value)}
            className="bg-white border border-slate-300 rounded-lg px-2.5 py-1 text-xs text-slate-700 font-medium focus:ring-1 focus:ring-violet-500 focus:outline-hidden"
          >
            <option value="">All Uploaded Documents</option>
            {documents.map((d) => (
              <option key={d.id} value={d.id}>
                {d.filename}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Message Stream */}
      <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-6">
        {messages.map((msg, i) => (
          <div
            key={i}
            className={`flex gap-3 sm:gap-4 ${
              msg.role === 'user' ? 'justify-end' : 'justify-start'
            }`}
          >
            {msg.role === 'assistant' && (
              <div className="w-8 h-8 rounded-xl bg-violet-600 text-white flex items-center justify-center shrink-0 shadow-xs mt-1">
                <Bot className="w-5 h-5" />
              </div>
            )}

            <div
              className={`max-w-[85%] sm:max-w-2xl rounded-2xl p-4 sm:p-5 shadow-xs text-sm leading-relaxed ${
                msg.role === 'user'
                  ? 'bg-violet-600 text-white rounded-br-none'
                  : 'bg-slate-50/90 border border-slate-200/80 text-slate-800 rounded-bl-none'
              }`}
            >
              {/* Message Header */}
              <div className="flex items-center justify-between text-[11px] mb-2 opacity-75">
                <span className="font-semibold">
                  {msg.role === 'user' ? 'You' : 'Cognivora AI'}
                </span>
                {msg.timestamp && <span>{msg.timestamp}</span>}
              </div>

              {/* Message Body */}
              <div className="whitespace-pre-wrap space-y-2">{msg.content}</div>

              {/* Source Citations Section */}
              {msg.citations && msg.citations.length > 0 && (
                <div className="mt-4 pt-3 border-t border-slate-200/60">
                  <p className="text-xs font-bold text-slate-600 flex items-center gap-1.5 mb-2">
                    <ShieldCheck className="w-4 h-4 text-emerald-600" />
                    <span>Grounded Sources ({msg.citations.length} Verified References):</span>
                  </p>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                    {msg.citations.map((c, idx) => (
                      <div
                        key={idx}
                        className="p-2.5 rounded-lg bg-white border border-slate-200 text-xs text-slate-700 space-y-1 shadow-2xs"
                      >
                        <div className="flex items-center justify-between font-semibold text-slate-900">
                          <span className="truncate max-w-[140px]">{c.document_name}</span>
                          <span className="text-[10px] px-1.5 py-0.5 rounded bg-violet-50 text-violet-700">
                            Page {c.page_number}
                          </span>
                        </div>
                        <p className="text-[11px] text-slate-500 line-clamp-2 italic">
                          "{c.excerpt}"
                        </p>
                        <div className="text-[10px] text-slate-400 text-right">
                          Similarity: {(c.similarity_score * 100).toFixed(0)}%
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Agent Decision Pill */}
              {msg.agent_decision && (
                <div className="mt-3 pt-2 flex items-center justify-between text-[11px]">
                  <span className="text-slate-400 italic truncate max-w-xs">
                    Intent: <span className="font-semibold text-violet-700">{msg.intent_detected}</span>
                  </span>
                  <button
                    onClick={() => setActiveDecision(msg)}
                    className="text-violet-600 hover:text-violet-800 font-semibold inline-flex items-center gap-1"
                  >
                    <Info className="w-3.5 h-3.5" />
                    <span>Inspect Agent Decision</span>
                  </button>
                </div>
              )}
            </div>

            {msg.role === 'user' && (
              <div className="w-8 h-8 rounded-xl bg-slate-900 text-white flex items-center justify-center shrink-0 shadow-xs mt-1">
                <User className="w-5 h-5" />
              </div>
            )}
          </div>
        ))}

        {loading && (
          <div className="flex gap-3 items-center text-slate-400 text-xs font-medium">
            <div className="w-8 h-8 rounded-xl bg-violet-100 text-violet-600 flex items-center justify-center animate-pulse">
              <Sparkles className="w-4 h-4" />
            </div>
            <span>Coordinator Agent is retrieving grounded context & synthesizing answer...</span>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Quick Prompt Chips */}
      <div className="px-4 py-2 bg-slate-50 border-t border-slate-100 flex items-center gap-2 overflow-x-auto text-xs">
        <span className="text-slate-400 shrink-0 font-semibold">Suggested:</span>
        {samplePrompts.map((p, idx) => (
          <button
            key={idx}
            onClick={() => handleSend(p)}
            className="px-2.5 py-1 rounded-full bg-white hover:bg-violet-50 border border-slate-200 text-slate-700 hover:text-violet-700 shrink-0 transition text-xs"
          >
            {p}
          </button>
        ))}
      </div>

      {/* Input Bar */}
      <div className="p-4 bg-white border-t border-slate-200/80">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSend();
          }}
          className="flex items-center gap-3"
        >
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask anything based on your course notes (e.g. 'Explain Banker's Algorithm with an example')..."
            className="flex-1 bg-slate-50 border border-slate-200 rounded-xl px-4 py-3 text-sm text-slate-800 focus:bg-white focus:outline-hidden focus:ring-2 focus:ring-violet-500"
            disabled={loading}
          />
          <button
            type="submit"
            disabled={loading || !input.trim()}
            className="px-5 py-3 rounded-xl bg-violet-600 hover:bg-violet-500 disabled:opacity-50 text-white font-semibold text-sm transition shadow-md shadow-violet-600/30 flex items-center gap-2 shrink-0"
          >
            <span>Ask</span>
            <Send className="w-4 h-4" />
          </button>
        </form>
      </div>

      {/* Agent Decision Modal */}
      {activeDecision && (
        <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-2xl border border-slate-200 space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <div className="flex items-center gap-2">
                <Info className="w-5 h-5 text-violet-600" />
                <h3 className="font-bold text-base text-slate-900">
                  Coordinator Agent Reasoning Trace
                </h3>
              </div>
              <button
                onClick={() => setActiveDecision(null)}
                className="text-slate-400 hover:text-slate-600"
              >
                ✕
              </button>
            </div>

            <div className="space-y-3 text-xs">
              <div>
                <span className="font-bold text-slate-400 uppercase">Intent Classified:</span>
                <p className="font-semibold text-slate-800 mt-0.5">{activeDecision.intent_detected}</p>
              </div>

              <div>
                <span className="font-bold text-slate-400 uppercase">Decision Rationale:</span>
                <p className="p-3 bg-slate-50 rounded-xl border border-slate-200 text-slate-700 mt-0.5 font-mono">
                  {activeDecision.agent_decision}
                </p>
              </div>

              <div>
                <span className="font-bold text-slate-400 uppercase">Model Runtime:</span>
                <p className="font-semibold text-slate-800 mt-0.5">{activeDecision.model_used}</p>
              </div>

              <div>
                <span className="font-bold text-slate-400 uppercase">Grounding Assurance:</span>
                <p className="font-semibold text-emerald-700 mt-0.5">
                  ✓ Verified against {activeDecision.citations?.length || 0} retrieved context chunks.
                </p>
              </div>
            </div>

            <div className="pt-2 text-right">
              <button
                onClick={() => setActiveDecision(null)}
                className="px-4 py-2 rounded-xl bg-violet-600 text-white font-semibold text-xs hover:bg-violet-700"
              >
                Done
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
