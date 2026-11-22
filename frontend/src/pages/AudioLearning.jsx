import React, { useState, useEffect, useRef } from 'react';
import { useLocation } from 'react-router-dom';
import {
  Volume2,
  Play,
  Pause,
  Square,
  RotateCcw,
  Sparkles,
  Sliders,
  Headphones,
  CheckCircle2,
  BookOpen,
  VolumeX
} from 'lucide-react';

const defaultLesson =
  "Operating Systems — Chapter 7: Deadlocks and Process Synchronization.\n\n" +
  "In a multiprogramming environment, several processes compete for a finite number of resources. " +
  "A process requests resources. If the resources are not available at that time, the process enters a waiting state. " +
  "Sometimes, a waiting process is never again able to change state, because the resources it has requested are held by other waiting processes. " +
  "This critical condition is called a deadlock.\n\n" +
  "There are four necessary conditions for deadlock to occur: Mutual Exclusion, Hold and Wait, No Preemption, and Circular Wait. " +
  "All four conditions must hold simultaneously for a deadlock situation to arise.\n\n" +
  "To handle deadlocks, systems employ either deadlock prevention, deadlock avoidance using Dijkstra's Banker's Algorithm, " +
  "or the ostrich algorithm which ignores the problem altogether.";

export default function AudioLearning() {
  const location = useLocation();
  const [text, setText] = useState(defaultLesson);
  const [title, setTitle] = useState('Chapter 7: Deadlocks Audio Lesson');

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
      setText(location.state.text);
      if (location.state.title) setTitle(location.state.title);
    }

    // Check browser Web Speech API support
    if (!('speechSynthesis' in window)) {
      setSupported(false);
      return;
    }

    const updateVoices = () => {
      const available = window.speechSynthesis.getVoices();
      setVoices(available);
      if (available.length > 0 && !selectedVoice) {
        // Prefer natural English voice if present
        const defaultV = available.find((v) => v.lang.includes('en') && (v.name.includes('Google') || v.name.includes('Natural') || v.name.includes('David'))) || available[0];
        setSelectedVoice(defaultV.name);
      }
    };

    updateVoices();
    window.speechSynthesis.onvoiceschanged = updateVoices;

    return () => {
      window.speechSynthesis.cancel();
    };
  }, [location.state]);

  const handlePlay = () => {
    if (!supported || !text.trim()) return;

    if (isPaused) {
      window.speechSynthesis.resume();
      setIsPaused(false);
      setIsPlaying(true);
      return;
    }

    window.speechSynthesis.cancel();

    const utterance = new SpeechSynthesisUtterance(text);
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

  const paragraphs = text.split('\n\n').filter((p) => p.trim());

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

      {/* Main Audio Player Card */}
      <div className="bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 text-white rounded-3xl p-6 sm:p-8 shadow-xl space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-2xl bg-violet-600 flex items-center justify-center shadow-lg shadow-violet-500/30">
              <Headphones className="w-6 h-6 text-white" />
            </div>
            <div>
              <span className="text-[11px] font-bold tracking-wider uppercase text-violet-400">
                Auditory Learning Suite
              </span>
              <h3 className="text-xl font-bold text-white">{title}</h3>
            </div>
          </div>

          {/* Dynamic Waveform Visualizer */}
          <div className="flex items-center gap-1.5 h-8 px-4 py-1.5 rounded-full bg-slate-800/80 border border-slate-700">
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

        {/* Playback Controls & Voice Settings */}
        <div className="p-4 rounded-2xl bg-slate-800/60 border border-slate-700/60 space-y-4">
          {/* Main Buttons */}
          <div className="flex flex-wrap items-center justify-center gap-4">
            {!isPlaying || isPaused ? (
              <button
                onClick={handlePlay}
                disabled={!supported}
                className="px-6 py-3 rounded-2xl bg-violet-600 hover:bg-violet-500 disabled:opacity-50 text-white font-bold text-sm transition shadow-lg shadow-violet-600/30 flex items-center gap-2"
              >
                <Play className="w-5 h-5 fill-white" />
                <span>{isPaused ? 'Resume Lesson' : 'Listen Spoken Lesson'}</span>
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
              <label className="block text-slate-400 font-medium mb-1">Narrator Voice:</label>
              <select
                value={selectedVoice}
                onChange={(e) => setSelectedVoice(e.target.value)}
                className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-xs text-slate-200"
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
        <div className="flex items-center justify-between pb-3 border-b border-slate-100">
          <div className="flex items-center gap-2">
            <BookOpen className="w-5 h-5 text-violet-600" />
            <h3 className="font-bold text-base text-slate-900">
              Synchronized Lesson Script
            </h3>
          </div>
          <span className="text-xs text-slate-400 font-medium">Editable script text</span>
        </div>

        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          rows={10}
          className="w-full p-4 rounded-xl bg-slate-50 border border-slate-200 text-sm text-slate-800 leading-relaxed focus:bg-white focus:outline-hidden focus:ring-2 focus:ring-violet-500 font-sans"
          placeholder="Paste or type any educational summary to listen to it as a spoken lesson..."
        />

        <div className="flex items-center justify-between text-xs text-slate-400 pt-2">
          <span>Words: {text.split(/\s+/).filter(Boolean).length}</span>
          <span>Estimated Audio Time: ~{Math.ceil(text.split(/\s+/).filter(Boolean).length / 140)} minutes</span>
        </div>
      </div>
    </div>
  );
}
