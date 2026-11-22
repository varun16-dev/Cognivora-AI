import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  TrendingUp,
  Award,
  AlertTriangle,
  CheckCircle2,
  Clock,
  ArrowRight,
  RefreshCw,
  BookOpen,
  Layers,
  ChevronRight
} from 'lucide-react';
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell
} from 'recharts';
import { api } from '../services/api';

export default function Analytics() {
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchAnalytics = async () => {
    setLoading(true);
    try {
      const res = await api.getAnalyticsDashboard();
      setData(res);
      setError(null);
    } catch (err) {
      console.error('Failed to load analytics:', err);
      setError('Could not connect to backend analytics service.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAnalytics();
  }, []);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[50vh] space-y-3">
        <RefreshCw className="w-8 h-8 text-violet-600 animate-spin" />
        <p className="text-sm font-medium text-slate-500">Calculating EWMA mastery scores & learning trajectories...</p>
      </div>
    );
  }

  const topicChartData = (data?.topic_mastery || []).map((t) => ({
    name: t.topic.length > 22 ? t.topic.slice(0, 20) + '...' : t.topic,
    mastery: t.mastery_percentage,
    status: t.status,
    fullName: t.topic
  }));

  const historyData = (data?.recent_quiz_history || []).slice(0, 10).reverse().map((h, i) => ({
    index: `Q${i + 1}`,
    score: h.percentage,
    title: h.quiz_title,
    date: new Date(h.completed_at).toLocaleDateString()
  }));

  return (
    <div className="max-w-6xl mx-auto space-y-8">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-black text-slate-900 tracking-tight">
          Adaptive Learning & Mastery Analytics
        </h2>
        <p className="text-sm text-slate-500 mt-1">
          Dynamic diagnostic telemetry calculated using Exponentially Weighted Moving Average (EWMA) formulas.
          Identifies subtopic knowledge gaps and prescribes personalized study interventions.
        </p>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-red-50 border border-red-200 text-red-700 text-sm">
          {error}
        </div>
      )}

      {/* High-Level Overview Banner */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-5">
        <div className="bg-white rounded-2xl p-6 border border-slate-200/80 shadow-xs">
          <p className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Overall Average Score</p>
          <p className="text-3xl font-black text-slate-900">{data?.average_quiz_score ?? 0}%</p>
          <p className="text-xs text-slate-500 mt-2">Across all attempted assessments</p>
        </div>

        <div className="bg-white rounded-2xl p-6 border border-slate-200/80 shadow-xs">
          <p className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Total Quizzes Evaluated</p>
          <p className="text-3xl font-black text-slate-900">{data?.total_quizzes_attempted ?? 0}</p>
          <p className="text-xs text-slate-500 mt-2">Stored and tracked in SQLite</p>
        </div>

        <div className="bg-white rounded-2xl p-6 border border-slate-200/80 shadow-xs">
          <p className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Identified Knowledge Gaps</p>
          <p className="text-3xl font-black text-amber-600">{data?.weak_topics?.length ?? 0}</p>
          <p className="text-xs text-slate-500 mt-2">Subtopics with &lt;60% accuracy threshold</p>
        </div>
      </div>

      {/* Visual Analytics Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Topic Mastery Chart */}
        <div className="bg-white rounded-2xl p-6 border border-slate-200/80 shadow-xs space-y-4">
          <div>
            <h3 className="font-bold text-base text-slate-900">Concept Mastery Distribution</h3>
            <p className="text-xs text-slate-400">EWMA formula: M_k = α·Score + (1-α)·M_prev</p>
          </div>

          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={topicChartData} margin={{ top: 10, right: 10, left: -20, bottom: 25 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                <XAxis dataKey="name" angle={-15} textAnchor="end" tick={{ fontSize: 10 }} />
                <YAxis domain={[0, 100]} tick={{ fontSize: 11 }} />
                <Tooltip formatter={(val) => [`${val}%`, 'Mastery Score']} />
                <Bar dataKey="mastery" radius={[6, 6, 0, 0]}>
                  {topicChartData.map((entry, idx) => {
                    const color =
                      entry.mastery >= 80 ? '#10b981' : entry.mastery >= 60 ? '#f59e0b' : '#ef4444';
                    return <Cell key={`cell-${idx}`} fill={color} />;
                  })}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className="flex items-center justify-center gap-6 text-xs font-medium text-slate-600 pt-2 border-t border-slate-100">
            <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-emerald-500"></span>Mastered (≥80%)</span>
            <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-amber-500"></span>Developing (60-79%)</span>
            <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-red-500"></span>Weak (&lt;60%)</span>
          </div>
        </div>

        {/* Rolling Progress Chart */}
        <div className="bg-white rounded-2xl p-6 border border-slate-200/80 shadow-xs space-y-4">
          <div>
            <h3 className="font-bold text-base text-slate-900">Historical Score Progression</h3>
            <p className="text-xs text-slate-400">Sequential accuracy over past 10 quiz attempts</p>
          </div>

          <div className="h-64 w-full">
            {historyData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={historyData} margin={{ top: 10, right: 10, left: -20, bottom: 25 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                  <XAxis dataKey="index" tick={{ fontSize: 11 }} />
                  <YAxis domain={[0, 100]} tick={{ fontSize: 11 }} />
                  <Tooltip formatter={(val) => [`${val}%`, 'Score']} />
                  <Line
                    type="monotone"
                    dataKey="score"
                    stroke="#7c3aed"
                    strokeWidth={3}
                    dot={{ r: 5, fill: '#7c3aed' }}
                  />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex flex-col items-center justify-center text-slate-400 text-xs">
                No quiz history available yet.
              </div>
            )}
          </div>
          <div className="text-center text-xs text-slate-400 pt-2 border-t border-slate-100">
            Scores automatically adjust the difficulty calibration of subsequent assessments.
          </div>
        </div>
      </div>

      {/* Weak Topics Diagnostic Cards */}
      {data?.weak_topics && data.weak_topics.length > 0 && (
        <div className="space-y-4">
          <h3 className="font-bold text-base text-slate-900 flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-amber-500" />
            <span>Targeted Topic Diagnostics (&lt;60% Accuracy)</span>
          </h3>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {data.weak_topics.map((t, i) => (
              <div
                key={i}
                className="p-5 rounded-2xl bg-amber-50/60 border border-amber-200 space-y-3"
              >
                <div className="flex items-center justify-between">
                  <span className="font-bold text-sm text-slate-900">{t}</span>
                  <span className="text-[11px] font-bold px-2 py-0.5 rounded bg-amber-200/80 text-amber-900">
                    Deficit
                  </span>
                </div>
                <p className="text-xs text-slate-600">
                  Prescription: Review high-yield notes and take an adaptive 5-question review quiz.
                </p>
                <div className="flex items-center gap-3 pt-1">
                  <button
                    onClick={() => navigate('/quiz')}
                    className="px-3.5 py-1.5 rounded-lg bg-amber-600 hover:bg-amber-700 text-white font-bold text-xs transition"
                  >
                    Take Adaptive Quiz
                  </button>
                  <button
                    onClick={() => navigate('/chat')}
                    className="px-3.5 py-1.5 rounded-lg border border-amber-300 text-amber-900 hover:bg-amber-100 text-xs font-semibold transition"
                  >
                    Ask AI Tutor
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Historical Quiz Table */}
      <div className="bg-white rounded-2xl border border-slate-200/80 shadow-xs overflow-hidden">
        <div className="p-5 border-b border-slate-100">
          <h3 className="font-bold text-base text-slate-900">Complete Assessment History</h3>
          <p className="text-xs text-slate-400">All recorded quiz attempts stored in SQLite database</p>
        </div>

        {data?.recent_quiz_history && data.recent_quiz_history.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-600">
              <thead className="bg-slate-50 text-xs font-bold text-slate-400 uppercase tracking-wider border-b border-slate-100">
                <tr>
                  <th className="px-6 py-3.5">Assessment Title</th>
                  <th className="px-6 py-3.5">Topic</th>
                  <th className="px-6 py-3.5">Difficulty</th>
                  <th className="px-6 py-3.5">Score</th>
                  <th className="px-6 py-3.5">Date</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {data.recent_quiz_history.map((h) => (
                  <tr key={h.attempt_id} className="hover:bg-slate-50 transition">
                    <td className="px-6 py-4 font-semibold text-slate-900">
                      {h.quiz_title}
                    </td>
                    <td className="px-6 py-4 text-xs font-medium text-slate-700">
                      {h.topic}
                    </td>
                    <td className="px-6 py-4">
                      <span className="px-2.5 py-0.5 rounded-full text-xs font-bold uppercase bg-slate-100 text-slate-700">
                        {h.difficulty}
                      </span>
                    </td>
                    <td className="px-6 py-4 font-bold text-xs">
                      <span
                        className={`px-2.5 py-1 rounded-full ${
                          h.percentage >= 80
                            ? 'bg-emerald-100 text-emerald-800'
                            : h.percentage >= 60
                            ? 'bg-amber-100 text-amber-800'
                            : 'bg-red-100 text-red-800'
                        }`}
                      >
                        {h.percentage}% ({h.score}/{h.total})
                      </span>
                    </td>
                    <td className="px-6 py-4 text-xs text-slate-400">
                      {new Date(h.completed_at).toLocaleString([], { dateStyle: 'short', timeStyle: 'short' })}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="p-8 text-center text-slate-400 text-sm">
            No quiz attempts recorded yet.
          </div>
        )}
      </div>
    </div>
  );
}
