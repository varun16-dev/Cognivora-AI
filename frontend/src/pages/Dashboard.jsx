import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  FileText,
  Award,
  Layers,
  TrendingUp,
  AlertTriangle,
  ArrowRight,
  BookOpen,
  CheckCircle2,
  Clock,
  Sparkles,
  RefreshCw
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

export default function Dashboard() {
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchDashboard = async () => {
    setLoading(true);
    try {
      const res = await api.getAnalyticsDashboard();
      setData(res);
      setError(null);
    } catch (err) {
      console.error('Failed to load dashboard:', err);
      setError('Could not connect to backend service. Please verify FastAPI is running on port 8000.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboard();
  }, []);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-3">
        <RefreshCw className="w-8 h-8 text-violet-600 animate-spin" />
        <p className="text-sm font-medium text-slate-500">Loading student analytics & mastery data...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 bg-red-50 border border-red-200 rounded-xl text-red-700">
        <div className="flex items-center gap-2 mb-2 font-semibold">
          <AlertTriangle className="w-5 h-5 text-red-600" />
          <span>Connection Error</span>
        </div>
        <p className="text-sm mb-4">{error}</p>
        <button
          onClick={fetchDashboard}
          className="px-4 py-2 bg-red-600 text-white rounded-lg text-sm font-medium hover:bg-red-700 transition"
        >
          Retry Connection
        </button>
      </div>
    );
  }

  const kpis = [
    {
      title: 'Uploaded Documents',
      value: data?.total_documents ?? 0,
      icon: FileText,
      color: 'from-blue-600 to-cyan-500',
      actionText: 'Manage Files',
      link: '/documents'
    },
    {
      title: 'Quizzes Attempted',
      value: data?.total_quizzes_attempted ?? 0,
      icon: Award,
      color: 'from-violet-600 to-purple-500',
      actionText: 'Take New Quiz',
      link: '/quiz'
    },
    {
      title: 'Average Quiz Score',
      value: `${data?.average_quiz_score ?? 0}%`,
      icon: TrendingUp,
      color: (data?.average_quiz_score ?? 0) >= 75 ? 'from-emerald-600 to-teal-500' : 'from-amber-600 to-orange-500',
      actionText: 'View History',
      link: '/analytics'
    },
    {
      title: 'Flashcards & Decks',
      value: data?.total_flashcards_created ?? 0,
      icon: Layers,
      color: 'from-indigo-600 to-violet-500',
      actionText: 'Study Cards',
      link: '/flashcards'
    },
  ];

  const chartData = (data?.topic_mastery || []).map((t) => ({
    topic: t.topic.length > 20 ? t.topic.slice(0, 18) + '...' : t.topic,
    mastery: t.mastery_percentage,
    status: t.status,
    fullTopic: t.topic
  }));

  const historyChartData = (data?.recent_quiz_history || []).slice(0, 6).reverse().map((h, i) => ({
    name: `Quiz ${i + 1}`,
    score: h.percentage,
    title: h.quiz_title,
    difficulty: h.difficulty
  }));

  return (
    <div className="space-y-8 max-w-7xl mx-auto">
      {/* Top Banner */}
      <div className="bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 rounded-2xl p-6 sm:p-8 text-white shadow-xl relative overflow-hidden">
        <div className="absolute right-0 top-0 bottom-0 w-1/3 bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-violet-500/20 via-transparent to-transparent pointer-events-none"></div>
        <div className="max-w-3xl relative z-10">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-violet-500/20 border border-violet-400/30 text-violet-300 text-xs font-semibold mb-3">
            <Sparkles className="w-3.5 h-3.5" />
            <span>Autonomous Multi-Agent Educational Suite</span>
          </div>
          <h2 className="text-2xl sm:text-3xl font-extrabold tracking-tight mb-2">
            Welcome to Cognivora AI Dashboard
          </h2>
          <p className="text-slate-300 text-sm sm:text-base leading-relaxed mb-6">
            Upload course materials, ask curriculum-grounded questions, generate multi-format quizzes,
            review 3D flashcards, and track your personalized mastery score calculated via adaptive EWMA modeling.
          </p>
          <div className="flex flex-wrap items-center gap-3">
            <button
              onClick={() => navigate('/chat')}
              className="px-5 py-2.5 rounded-xl bg-violet-600 hover:bg-violet-500 text-white font-semibold text-sm transition shadow-lg shadow-violet-600/30 flex items-center gap-2"
            >
              <span>Ask AI Study Assistant</span>
              <ArrowRight className="w-4 h-4" />
            </button>
            <button
              onClick={() => navigate('/documents')}
              className="px-5 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 font-semibold text-sm transition"
            >
              Upload New Document
            </button>
          </div>
        </div>
      </div>

      {/* KPI Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        {kpis.map((kpi, idx) => {
          const Icon = kpi.icon;
          return (
            <div
              key={idx}
              className="bg-white rounded-2xl p-5 border border-slate-200/80 shadow-xs hover:shadow-md transition-all duration-200 flex flex-col justify-between"
            >
              <div className="flex items-center justify-between mb-4">
                <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                  {kpi.title}
                </span>
                <div className={`w-10 h-10 rounded-xl bg-gradient-to-tr ${kpi.color} text-white flex items-center justify-center shadow-xs`}>
                  <Icon className="w-5 h-5" />
                </div>
              </div>
              <div>
                <p className="text-3xl font-black text-slate-900 tracking-tight mb-3">
                  {kpi.value}
                </p>
                <button
                  onClick={() => navigate(kpi.link)}
                  className="inline-flex items-center gap-1.5 text-xs font-semibold text-violet-600 hover:text-violet-700 transition"
                >
                  <span>{kpi.actionText}</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          );
        })}
      </div>

      {/* Weak Topics Revision Alert */}
      {data?.weak_topics && data.weak_topics.length > 0 && (
        <div className="bg-amber-50/80 border border-amber-200 rounded-2xl p-5 shadow-xs">
          <div className="flex items-start justify-between gap-4 flex-wrap">
            <div className="flex items-start gap-3">
              <div className="w-9 h-9 rounded-xl bg-amber-500 text-white flex items-center justify-center shrink-0 shadow-xs">
                <AlertTriangle className="w-5 h-5" />
              </div>
              <div>
                <h4 className="font-bold text-slate-900 text-sm sm:text-base">
                  Adaptive Learning Alert: Knowledge Deficits Detected (&lt;60% Mastery)
                </h4>
                <p className="text-xs sm:text-sm text-slate-600 mt-0.5">
                  The adaptive engine recommends targeted revision on these concepts before attempting difficult assessments:
                </p>
                <div className="flex flex-wrap gap-2 mt-3">
                  {data.weak_topics.map((t, idx) => (
                    <span
                      key={idx}
                      className="px-2.5 py-1 rounded-md bg-amber-100/90 text-amber-900 text-xs font-semibold border border-amber-200"
                    >
                      ⚠️ {t}
                    </span>
                  ))}
                </div>
              </div>
            </div>
            <button
              onClick={() => navigate('/quiz')}
              className="px-4 py-2 rounded-xl bg-amber-600 hover:bg-amber-700 text-white text-xs font-bold transition shadow-xs shrink-0"
            >
              Start Diagnostic Review Quiz
            </button>
          </div>
        </div>
      )}

      {/* Visual Analytics Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Topic Mastery Bar Chart */}
        <div className="bg-white rounded-2xl p-6 border border-slate-200/80 shadow-xs">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="font-bold text-base text-slate-900">Topic Readiness Breakdown</h3>
              <p className="text-xs text-slate-400">Curricular mastery percentage per concept node</p>
            </div>
            <span className="text-xs px-2.5 py-1 rounded-full bg-slate-100 font-semibold text-slate-600">
              EWMA Calculated
            </span>
          </div>

          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 20 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                <XAxis dataKey="topic" angle={-15} textAnchor="end" tick={{ fontSize: 11 }} />
                <YAxis domain={[0, 100]} tick={{ fontSize: 11 }} />
                <Tooltip
                  formatter={(val) => [`${val}%`, 'Mastery Score']}
                  labelFormatter={(lbl) => `Topic: ${lbl}`}
                />
                <Bar dataKey="mastery" radius={[6, 6, 0, 0]}>
                  {chartData.map((entry, index) => {
                    const color =
                      entry.mastery >= 80 ? '#10b981' : entry.mastery >= 60 ? '#f59e0b' : '#ef4444';
                    return <Cell key={`cell-${index}`} fill={color} />;
                  })}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
          <div className="flex items-center justify-center gap-6 text-xs font-medium text-slate-600 pt-3 border-t border-slate-100">
            <div className="flex items-center gap-1.5">
              <span className="w-3 h-3 rounded-full bg-emerald-500"></span>
              <span>Mastered (≥80%)</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-3 h-3 rounded-full bg-amber-500"></span>
              <span>Developing (60-79%)</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-3 h-3 rounded-full bg-red-500"></span>
              <span>Needs Review (&lt;60%)</span>
            </div>
          </div>
        </div>

        {/* Score History Line Chart */}
        <div className="bg-white rounded-2xl p-6 border border-slate-200/80 shadow-xs">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="font-bold text-base text-slate-900">Quiz Performance Trajectory</h3>
              <p className="text-xs text-slate-400">Score percentage across recent assessments</p>
            </div>
            <button
              onClick={() => navigate('/quiz')}
              className="text-xs text-violet-600 font-semibold hover:underline"
            >
              Take Quiz →
            </button>
          </div>

          <div className="h-64 w-full">
            {historyChartData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={historyChartData} margin={{ top: 10, right: 10, left: -20, bottom: 20 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                  <XAxis dataKey="name" tick={{ fontSize: 11 }} />
                  <YAxis domain={[0, 100]} tick={{ fontSize: 11 }} />
                  <Tooltip formatter={(val) => [`${val}%`, 'Score']} />
                  <Line
                    type="monotone"
                    dataKey="score"
                    stroke="#7c3aed"
                    strokeWidth={3}
                    dot={{ r: 5, fill: '#7c3aed' }}
                    activeDot={{ r: 7 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex flex-col items-center justify-center text-slate-400 space-y-2">
                <Award className="w-10 h-10 stroke-1" />
                <p className="text-xs font-medium">No quiz attempts recorded yet.</p>
                <button
                  onClick={() => navigate('/quiz')}
                  className="px-3 py-1.5 rounded-lg bg-violet-600 text-white text-xs font-semibold"
                >
                  Take Your First Quiz
                </button>
              </div>
            )}
          </div>
          <div className="text-center text-xs text-slate-400 pt-3 border-t border-slate-100">
            Scores automatically feed into the Adaptive Learning Engine.
          </div>
        </div>
      </div>

      {/* Recommendations & Action Plan */}
      <div className="bg-white rounded-2xl p-6 border border-slate-200/80 shadow-xs">
        <h3 className="font-bold text-base text-slate-900 mb-1">
          Personalized Action Plan & Study Recommendations
        </h3>
        <p className="text-xs text-slate-400 mb-4">
          Generated automatically by Coordinator Agent based on historical quiz diagnostics
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {data?.improvement_recommendations?.map((rec, i) => (
            <div
              key={i}
              className="flex items-start gap-3 p-4 rounded-xl bg-slate-50 border border-slate-200/70"
            >
              <div className="w-7 h-7 rounded-lg bg-violet-100 text-violet-700 flex items-center justify-center shrink-0 font-bold text-xs mt-0.5">
                {i + 1}
              </div>
              <div className="flex-1">
                <p className="text-xs sm:text-sm font-semibold text-slate-800 leading-snug">{rec}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
