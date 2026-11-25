import React, { useState, useEffect } from 'react';
import { useLocation, Link } from 'react-router-dom';
import {
  Play,
  Pause,
  Square,
  Headphones,
  BookOpen,
  VolumeX,
  UploadCloud,
  Sparkles,
  RefreshCw
} from 'lucide-react';
import { api } from '../services/api';

const extractCleanTitle = (doc) => {
  if (!doc) return 'Audio Lesson';

  // 1. Check doc.topics for non-generic topics
  if (doc.topics && Array.isArray(doc.topics)) {
    for (const t of doc.topics) {
      if (!t || typeof t !== 'string') continue;
      const cleaned = t
        .replace(/^[\s#\-\u2013\u2014\*\•\d\.\/:]*(?:Module|Chapter|Unit|Section)?[\s\-\u2013\u2014\d:\.]*/gi, '')
        .trim();
      const lower = cleaned.toLowerCase();
      if (
        cleaned.length > 3 &&
        !lower.includes('general studies') &&
        !lower.startsWith('general') &&
        !lower.includes('course material') &&
        !lower.includes('lecture notes')
      ) {
        return cleaned;
      }
    }
  }

  // 2. Check doc.subject if specific
  if (doc.subject && typeof doc.subject === 'string') {
    const s = doc.subject.trim();
    const sLower = s.toLowerCase();
    if (s.length > 2 && sLower !== 'general studies' && sLower !== 'general' && sLower !== 'unknown') {
      return s;
    }
  }

  // 3. Fallback to clean filename
  let name = doc.filename || '';
  name = name.replace(/\.(pdf|docx|txt)$/i, '');
  // Strip leading prefixes like Lecture Material_BAI701_, LectureNotes_BAD703_, etc.
  name = name.replace(/^(?:(?:Lecture\s*Material|LectureNotes|Lecture|Unit|Module|Section|Part)[\s\d\-–—]*|[A-Z]{2,4}\d{3,}[_\s\-–—]*)+/gi, '');
  // Strip author signatures like Prepared by Prof. Sathiya or Dr. Sivaprakash
  name = name.replace(/(?:Prepared\s+by|Dr\.|Prof\.|Professor)[\s\S]*$/gi, '');
  name = name.replace(/Part[\s_-]*\d+$/gi, '');
  name = name.replace(/[_\-]+/g, ' ').trim();

  return name || doc.filename || 'Audio Lesson';
};

const formatForAudioLesson = (rawText, cleanTitle = '') => {
  if (!rawText || !rawText.trim()) return '';

  let text = rawText;

  // 1. Remove slide header blocks and metadata lines
  text = text.replace(/\b(?:BAD|BAI|[A-Z]{2,4})\d{3,4}[\s\S]*?(?:Dr\.|Prof\.|Professor)\b\s*/gi, '');
  text = text.replace(/^[ \t]*[-*•]?\s*(?:BAD|BAI|[A-Z]{2,4})\d{3,4}[^\n]*$/gmi, '');
  text = text.replace(/^[ \t]*[-*•]?\s*(?:Dr\.|Prof\.|Professor)[^\n]*$/gmi, '');
  text = text.replace(/^[ \t]*[-*•]?\s*Module\s*[\-\u2013\u2014\d:\.]*$/gmi, '');
  text = text.replace(/^[ \t]*\*{0,2}(?:Source\s+)?Document:\*{0,2}[^\n]*$/gmi, '');

  // 2. Main title: single #
  text = text.replace(/^#\s+[\-\u2013\u2014\s\d:\.]*(?:Module|Chapter|Unit|Section)?[\s\-\u2013\u2014\d:\.]*(.*?)(?::\s*Academic Summary|:\s*Summary)?$/gmi, (m, t) => {
    const title = t.trim() || cleanTitle || 'Audio Study Lesson';
    return `${title} — Spoken Audio Study Lesson.\n\n`;
  });

  // 3. Subheadings with clean trailing newlines
  text = text.replace(/^###?\s*Overview\s*(?:&|and)\s*Key\s*Concepts\s*:?/gmi, 'Overview and Key Concepts:\n\n');
  text = text.replace(/^###?\s*High-Yield\s*Key\s*Points\s*:?/gmi, 'Key Takeaways and Focus Points:\n\n');
  text = text.replace(/^###?\s*Key\s*Takeaways\s*:?/gmi, 'Key Takeaways and Focus Points:\n\n');
  text = text.replace(/^#{2,6}\s*(.*?):?$/gmi, '$1:\n\n');

  // 4. Strip inline formatting
  text = text.replace(/\*\*([^*]+)\*\*/g, '$1');
  text = text.replace(/\*([^*]+)\*/g, '$1');
  text = text.replace(/__([^_]+)__/g, '$1');
  text = text.replace(/`([^`]+)`/g, '$1');

  // 5. Clean bullets
  text = text.replace(/^[ \t]*[-*•]\s+/gmi, '• ');

  const rawParagraphs = text.split(/\n{2,}/);
  const cleaned = [];
  const seen = new Set();

  for (const p of rawParagraphs) {
    const lines = p.split('\n').map((l) => l.trim()).filter(Boolean);
    if (lines.length === 0) continue;

    const bulletLines = lines.filter((l) => l.startsWith('• '));
    const proseLines = lines.filter((l) => !l.startsWith('• '));

    if (proseLines.length > 0) {
      const filteredProse = proseLines.filter((l) => {
        if (/\b(?:BAD|BAI|[A-Z]{2,4})\d{3,4}\b/i.test(l)) return false;
        if (/^(?:Dr\.|Prof\.|Professor)\s*$/i.test(l)) return false;
        if (/^Module\s*[\-\u2013\u2014\d:\.]*$/i.test(l)) return false;
        return true;
      });

      if (filteredProse.length > 0) {
        const fullPara = filteredProse.join(' ');
        const lower = fullPara.toLowerCase();
        if (lower.length > 30) {
          seen.add(lower);
        }
        cleaned.push(fullPara);
      }
    }

    if (bulletLines.length > 0) {
      const keptBullets = [];
      for (const b of bulletLines) {
        const core = b.substring(2).trim();
        if (/\b(?:BAD|BAI|[A-Z]{2,4})\d{3,4}\b/i.test(core)) continue;
        if (/^(?:Dr\.|Prof\.|Professor)\s*$/i.test(core)) continue;
        const lower = core.toLowerCase();
        // Check if this bullet was already covered in the prose overview
        let duplicate = false;
        if (seen.has(lower)) duplicate = true;
        for (const prev of seen) {
          if (prev.includes(lower) || lower.includes(prev)) {
            duplicate = true;
            break;
          }
        }
        if (duplicate) continue;
        seen.add(lower);
        keptBullets.push(`• ${core}`);
      }
      if (keptBullets.length > 0) {
        cleaned.push(keptBullets.join('\n'));
      }
    }
  }

  let result = cleaned.join('\n\n').trim();

  // If text does not start with a clean title header, prepend one
  if (cleanTitle && !result.toLowerCase().startsWith(cleanTitle.toLowerCase())) {
    result = `${cleanTitle} — Spoken Audio Study Lesson.\n\n${result}`;
  }

  return result;
};

const buildDefaultScript = (doc) => {
  if (!doc) return '';
  const cleanTitle = extractCleanTitle(doc);
  const topicsList = (doc.topics && doc.topics.length > 0 && !doc.topics[0].toLowerCase().includes('general'))
    ? doc.topics.map(t => t.replace(/^[\s#\-\u2013\u2014\*\•\d\.\/:]*(?:Module|Chapter|Unit|Section)?[\s\-\u2013\u2014\d:\.]*/gi, '').trim()).filter(Boolean).slice(0, 4).join(', ')
    : 'theoretical foundations, architectural mechanisms, and practical methodologies';

  return (
    `${cleanTitle} — Spoken Audio Study Lesson.\n\n` +
    `Welcome to the audio study session for ${cleanTitle}.\n\n` +
    `This lecture explores the fundamental principles and technical mechanisms outlined in your course materials, focusing on: ${topicsList}.\n\n` +
    `Key Focus Areas for Review:\n` +
    `• Theoretical foundations, formal criteria, and architectural principles.\n` +
    `• Operational workflows, algorithmic procedures, and sequence analysis.\n` +
    `• Practical implementation trade-offs, security considerations, and system performance.\n\n` +
    `To generate a comprehensive, in-depth audio lecture synthesized directly from your slides, click 'Generate Full In-Depth Lesson' above, or edit this script directly before listening.`
  );
};

export default function AudioLearning() {
  const location = useLocation();
  const [documents, setDocuments] = useState([]);
  const [selectedDocId, setSelectedDocId] = useState('');
  const [text, setText] = useState(location.state?.text || '');
  const [title, setTitle] = useState(location.state?.title || 'Audio Learning Lab');
  const [generating, setGenerating] = useState(false);

  // Audio Speech state
  const [voices, setVoices] = useState([]);
  const [selectedVoice, setSelectedVoice] = useState('');
  const [rate, setRate] = useState(1.0);
  const [pitch, setPitch] = useState(1.0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [supported, setSupported] = useState(true);

  useEffect(() => {
    // If navigated from Summaries page with preloaded text
    if (location.state?.text) {
      const initialTitle = location.state.title || 'Audio Lesson';
      const cleanTitle = initialTitle.replace(/^[\s#\-\u2013\u2014\*\•\d\.\/:]*(?:Module|Chapter|Unit|Section)?[\s\-\u2013\u2014\d:\.]*/gi, '').trim() || initialTitle;
      setText(formatForAudioLesson(location.state.text, cleanTitle));
      setTitle(cleanTitle.endsWith('Audio Lesson') ? cleanTitle : `${cleanTitle} — Audio Lesson`);
    } else {
      // Check for uploaded documents
      api.getDocuments()
        .then(async (docs) => {
          setDocuments(docs || []);
          if (docs && docs.length > 0) {
            const first = docs[0];
            setSelectedDocId(first.id);
            const cleanTitle = extractCleanTitle(first);
            setTitle(`${cleanTitle} — Audio Lesson`);

            // Try to load any previously saved summary for this document
            try {
              const summaries = await api.getSummaries();
              const matchingSummary = summaries.find((s) => s.document_id === first.id);
              if (matchingSummary && matchingSummary.content && matchingSummary.content.trim()) {
                setText(formatForAudioLesson(matchingSummary.content, cleanTitle));
                return;
              }
            } catch (err) {
              console.log('Could not load summaries:', err);
            }

            // Fallback to structured study script (never show raw metadata)
            setText(buildDefaultScript(first));
          } else {
            setText('');
            setTitle('Auditory Learning Suite');
          }
        })
        .catch((err) => console.log('Could not load documents for audio:', err));
    }

    // Check browser Web Speech API support
    if (!('speechSynthesis' in window)) {
      setSupported(false);
      return;
    }

    const updateVoices = () => {
      const available = window.speechSynthesis.getVoices();
      if (!available || available.length === 0) return;

      // Filter and prioritize English voices
      const englishVoices = available.filter((v) => v.lang.toLowerCase().startsWith('en'));
      const voiceList = englishVoices.length > 0 ? englishVoices : available;
      setVoices(voiceList);

      if (!selectedVoice || !voiceList.some((v) => v.name === selectedVoice)) {
        const defaultV =
          voiceList.find((v) => v.name.includes('Google') || v.name.includes('Natural') || v.name.includes('David') || v.name.includes('Jenny') || v.name.includes('Zira')) ||
          voiceList[0];
        if (defaultV) {
          setSelectedVoice(defaultV.name);
        }
      }
    };

    updateVoices();
    window.speechSynthesis.onvoiceschanged = updateVoices;

    return () => {
      window.speechSynthesis.cancel();
    };
  }, [location.state]);

  const handleDocumentSelect = async (docId) => {
    setSelectedDocId(docId);
    const doc = documents.find((d) => d.id === docId);
    if (!doc) return;

    const cleanTitle = extractCleanTitle(doc);
    setTitle(`${cleanTitle} — Audio Lesson`);

    // Check if there is an existing summary for this document
    try {
      const summaries = await api.getSummaries();
      const matchingSummary = summaries.find((s) => s.document_id === doc.id);
      if (matchingSummary && matchingSummary.content && matchingSummary.content.trim()) {
        setText(formatForAudioLesson(matchingSummary.content, cleanTitle));
      } else {
        setText(buildDefaultScript(doc));
      }
    } catch {
      setText(buildDefaultScript(doc));
    }

    if (isPlaying || isPaused) {
      window.speechSynthesis.cancel();
      setIsPlaying(false);
      setIsPaused(false);
    }
  };

  const handleGenerateInDepthLesson = async () => {
    const doc = documents.find((d) => d.id === selectedDocId);
    if (!doc) return;

    setGenerating(true);
    const cleanTitle = extractCleanTitle(doc);

    try {
      const res = await api.generateSummary({
        document_id: doc.id,
        topic: cleanTitle,
        mode: 'detailed'
      });
      if (res && res.content) {
        setText(formatForAudioLesson(res.content, cleanTitle));
        setTitle(`${cleanTitle} — In-Depth Audio Lesson`);
      }
    } catch (err) {
      console.error('Failed to generate in-depth summary:', err);
    } finally {
      setGenerating(false);
    }
  };

  const handlePlay = () => {
    if (!supported || !text.trim()) return;

    if (isPaused) {
      window.speechSynthesis.resume();
      setIsPaused(false);
      setIsPlaying(true);
      return;
    }

    window.speechSynthesis.cancel();

    // Prepare clean speech text: remove bullet symbols and markdown artifacts so voice is fluent
    const spokenText = text
      .replace(/^[ \t]*•\s*/gmi, '')
      .replace(/•/g, '')
      .replace(/[#*_~`]/g, '')
      .replace(/\s+/g, ' ')
      .trim();

    const utterance = new SpeechSynthesisUtterance(spokenText);
    utterance.rate = rate;
    utterance.pitch = pitch;

    if (selectedVoice) {
      const vObj = voices.find((v) => v.name === selectedVoice);
      if (vObj) utterance.voice = vObj;
    }

    utterance.onstart = () => {
      setIsPlaying(true);
      setIsPaused(false);
    };

    utterance.onend = () => {
      setIsPlaying(false);
      setIsPaused(false);
    };

    utterance.onerror = () => {
      setIsPlaying(false);
      setIsPaused(false);
    };

    window.speechSynthesis.speak(utterance);
  };

  const handlePause = () => {
    if (isPlaying && !isPaused) {
      window.speechSynthesis.pause();
      setIsPaused(true);
    }
  };

  const handleStop = () => {
    window.speechSynthesis.cancel();
    setIsPlaying(false);
    setIsPaused(false);
  };

  const selectedDoc = documents.find((d) => d.id === selectedDocId);

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      {/* Page Header */}
      <div>
        <h2 className="text-2xl font-black text-slate-900 tracking-tight">
          Audio Learning Lab & Spoken Lessons
        </h2>
        <p className="text-sm text-slate-500 mt-1">
          Convert textbook summaries and concept notes into synthesized spoken lessons using the browser Web Speech API.
          Ideal for auditory learners and active commute revision.
        </p>
      </div>

      {!supported && (
        <div className="p-4 rounded-xl bg-amber-50 border border-amber-200 text-amber-800 text-sm flex items-center gap-2">
          <VolumeX className="w-5 h-5 text-amber-600 shrink-0" />
          <span>
            Your current browser does not natively support the Web Speech API. Please use Google Chrome, Edge, or Safari for full audio synthesis.
          </span>
        </div>
      )}

      {/* When no text or documents are available */}
      {documents.length === 0 && !text.trim() && (
        <div className="p-6 rounded-2xl bg-white border border-slate-200/80 shadow-xs flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-violet-100 text-violet-700 flex items-center justify-center shrink-0">
              <UploadCloud className="w-5 h-5" />
            </div>
            <div>
              <h4 className="font-bold text-sm text-slate-900">No Document Uploaded Yet</h4>
              <p className="text-xs text-slate-500 mt-0.5">
                Upload your course PDF or DOCX to auto-generate spoken audio lessons, or type study notes directly below.
              </p>
            </div>
          </div>
          <Link
            to="/documents"
            className="px-4 py-2.5 rounded-xl bg-violet-600 hover:bg-violet-700 text-white font-bold text-xs transition shadow-xs shrink-0 flex items-center gap-1.5"
          >
            <UploadCloud className="w-4 h-4" />
            <span>Upload Course Material</span>
          </Link>
        </div>
      )}

      {/* Main Audio Player Card */}
      <div className="bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 text-white rounded-3xl p-6 sm:p-8 shadow-xl space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-3 min-w-0">
            <div className="w-12 h-12 rounded-2xl bg-violet-600 flex items-center justify-center shadow-lg shadow-violet-500/30 shrink-0">
              <Headphones className="w-6 h-6 text-white" />
            </div>
            <div className="min-w-0">
              <span className="text-[11px] font-bold tracking-wider uppercase text-violet-400">
                Auditory Learning Suite
              </span>
              <h3 className="text-xl font-bold text-white truncate">{title}</h3>
            </div>
          </div>

          {/* Dynamic Waveform Visualizer */}
          <div className="flex items-center gap-1.5 h-8 px-4 py-1.5 rounded-full bg-slate-800/80 border border-slate-700 shrink-0">
            {[40, 70, 30, 90, 60, 100, 50, 80, 45, 65].map((h, i) => (
              <span
                key={i}
                className={`w-1 rounded-full bg-violet-400 transition-all duration-200 ${
                  isPlaying && !isPaused ? 'animate-pulse' : 'opacity-40'
                }`}
                style={{
                  height: isPlaying && !isPaused ? `${Math.max(20, (h * (i % 2 === 0 ? 1 : 0.6)))}%` : '25%'
                }}
              ></span>
            ))}
            <span className="text-[11px] font-semibold text-slate-300 ml-2">
              {isPlaying ? (isPaused ? 'Paused' : 'Playing') : 'Ready'}
            </span>
          </div>
        </div>

        {/* Source Document Selector if documents exist */}
        {documents.length > 0 && (
          <div className="flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-3 p-3.5 rounded-2xl bg-slate-800/50 border border-slate-700/60 min-w-0">
            <span className="text-xs text-slate-300 font-semibold shrink-0">Document Audio Source:</span>
            <div className="flex-1 min-w-0">
              <select
                value={selectedDocId}
                onChange={(e) => handleDocumentSelect(e.target.value)}
                className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-xs text-slate-200 font-medium focus:ring-1 focus:ring-violet-500 truncate"
              >
                {documents.map((d) => (
                  <option key={d.id} value={d.id}>
                    {extractCleanTitle(d)} — {d.filename}
                  </option>
                ))}
              </select>
            </div>
          </div>
        )}

        {/* Playback Controls & Voice Settings */}
        <div className="p-4 rounded-2xl bg-slate-800/60 border border-slate-700/60 space-y-4">
          {/* Main Buttons */}
          <div className="flex flex-wrap items-center justify-center gap-4">
            {!isPlaying || isPaused ? (
              <button
                onClick={handlePlay}
                disabled={!supported || !text.trim()}
                className="px-6 py-3 rounded-2xl bg-violet-600 hover:bg-violet-500 disabled:opacity-40 text-white font-bold text-sm transition shadow-lg shadow-violet-600/30 flex items-center gap-2"
              >
                <Play className="w-5 h-5 fill-white" />
                <span>
                  {isPaused ? 'Resume Lesson' : text.trim() ? 'Listen Spoken Lesson' : 'Upload or Enter Notes to Listen'}
                </span>
              </button>
            ) : (
              <button
                onClick={handlePause}
                className="px-6 py-3 rounded-2xl bg-amber-600 hover:bg-amber-500 text-white font-bold text-sm transition shadow-lg shadow-amber-600/30 flex items-center gap-2"
              >
                <Pause className="w-5 h-5 fill-white" />
                <span>Pause</span>
              </button>
            )}

            <button
              onClick={handleStop}
              disabled={!isPlaying && !isPaused}
              className="px-5 py-3 rounded-2xl bg-slate-700 hover:bg-slate-600 disabled:opacity-40 text-slate-200 font-semibold text-sm transition flex items-center gap-2"
            >
              <Square className="w-4 h-4 fill-slate-300" />
              <span>Stop</span>
            </button>
          </div>

          {/* Sliders Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-3 border-t border-slate-700/60 text-xs">
            {/* Voice Dropdown */}
            <div>
              <label className="block text-slate-400 font-medium mb-1">Narrator Voice (English):</label>
              <select
                value={selectedVoice}
                onChange={(e) => setSelectedVoice(e.target.value)}
                className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-xs text-slate-200 truncate"
              >
                {voices.map((v) => (
                  <option key={v.name} value={v.name}>
                    {v.name} ({v.lang})
                  </option>
                ))}
              </select>
            </div>

            {/* Speed Rate Slider */}
            <div>
              <div className="flex justify-between text-slate-400 font-medium mb-1">
                <span>Speed Rate:</span>
                <span className="text-violet-400 font-bold">{rate.toFixed(2)}x</span>
              </div>
              <input
                type="range"
                min="0.75"
                max="1.75"
                step="0.05"
                value={rate}
                onChange={(e) => setRate(parseFloat(e.target.value))}
                className="w-full accent-violet-500"
              />
            </div>

            {/* Pitch Slider */}
            <div>
              <div className="flex justify-between text-slate-400 font-medium mb-1">
                <span>Voice Pitch:</span>
                <span className="text-violet-400 font-bold">{pitch.toFixed(1)}</span>
              </div>
              <input
                type="range"
                min="0.8"
                max="1.2"
                step="0.05"
                value={pitch}
                onChange={(e) => setPitch(parseFloat(e.target.value))}
                className="w-full accent-violet-500"
              />
            </div>
          </div>
        </div>
      </div>

      {/* Synchronized Lesson Script Reader */}
      <div className="bg-white rounded-2xl p-6 sm:p-8 border border-slate-200/80 shadow-xs space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-3 border-b border-slate-100 gap-3">
          <div className="flex items-center gap-2">
            <BookOpen className="w-5 h-5 text-violet-600" />
            <h3 className="font-bold text-base text-slate-900">
              Synchronized Lesson Script
            </h3>
          </div>
          <div className="flex items-center gap-3">
            {selectedDoc && (
              <button
                type="button"
                onClick={handleGenerateInDepthLesson}
                disabled={generating}
                className="px-3.5 py-1.5 rounded-xl bg-violet-50 hover:bg-violet-100 text-violet-700 font-bold text-xs border border-violet-200 transition flex items-center gap-1.5 shadow-2xs"
              >
                {generating ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Sparkles className="w-3.5 h-3.5 text-violet-600" />}
                <span>{generating ? 'Generating Lesson...' : '⚡ Generate Full In-Depth Lesson'}</span>
              </button>
            )}
            <span className="text-xs text-slate-400 font-medium">Editable script text</span>
          </div>
        </div>

        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          rows={9}
          className="w-full p-4 rounded-xl bg-slate-50 border border-slate-200 text-sm text-slate-800 leading-relaxed focus:bg-white focus:outline-hidden focus:ring-2 focus:ring-violet-500 font-sans"
          placeholder="No text loaded yet. Upload a course document, generate an in-depth lesson, or paste your study notes here to listen..."
        />

        <div className="flex items-center justify-between text-xs text-slate-400 pt-2">
          <span>Words: {text.split(/\s+/).filter(Boolean).length}</span>
          <span>Estimated Audio Time: ~{Math.ceil(text.split(/\s+/).filter(Boolean).length / 140)} minutes</span>
        </div>
      </div>
    </div>
  );
}
