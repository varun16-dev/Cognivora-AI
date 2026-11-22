import React, { useState, useEffect } from 'react';
import { NavLink, Outlet, useLocation } from 'react-router-dom';
import {
  LayoutDashboard,
  UploadCloud,
  MessageSquare,
  Award,
  Layers,
  FileText,
  Volume2,
  TrendingUp,
  Cpu,
  ExternalLink,
  Menu,
  X
} from 'lucide-react';
import { api } from '../services/api';

const navigation = [
  { name: 'Dashboard', href: '/', icon: LayoutDashboard },
  { name: 'Upload Documents', href: '/documents', icon: UploadCloud },
  { name: 'AI Study Chat', href: '/chat', icon: MessageSquare },
  { name: 'Quiz Generator', href: '/quiz', icon: Award },
  { name: 'Flashcards', href: '/flashcards', icon: Layers },
  { name: 'AI Summaries', href: '/summaries', icon: FileText },
  { name: 'Audio Learning', href: '/audio', icon: Volume2 },
  { name: 'Study Analytics', href: '/analytics', icon: TrendingUp },
];

export default function Layout() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [health, setHealth] = useState({
    active_model: 'Gemini 2.5 Flash',
    gemini_api_configured: false,
    vector_store: 'ChromaDB'
  });
  const location = useLocation();

  useEffect(() => {
    api.getHealth()
      .then((data) => setHealth(data))
      .catch((err) => console.log('Backend health check:', err));
  }, []);

  return (
    <div className="flex h-screen bg-slate-50 text-slate-800 font-sans overflow-hidden">
      {/* Sidebar Desktop */}
      <aside className="hidden md:flex md:w-64 flex-col bg-slate-900 border-r border-slate-800 text-white select-none">
        {/* Brand */}
        <div className="p-5 flex items-center gap-3 border-b border-slate-800/80">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-violet-600 to-indigo-500 flex items-center justify-center shadow-lg shadow-violet-500/30">
            <Cpu className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="font-bold text-lg tracking-tight bg-gradient-to-r from-white via-slate-100 to-slate-400 bg-clip-text text-transparent">
              Cognivora AI
            </h1>
            <p className="text-[11px] text-violet-400 font-medium tracking-wide uppercase">
              Agentic Learning Hub
            </p>
          </div>
        </div>

        {/* Nav Links */}
        <nav className="flex-1 p-3 space-y-1 overflow-y-auto">
          {navigation.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.href;
            return (
              <NavLink
                key={item.name}
                to={item.href}
                className={`flex items-center gap-3 px-3.5 py-2.5 rounded-lg text-sm font-medium transition-all duration-150 ${
                  isActive
                    ? 'bg-violet-600 text-white shadow-md shadow-violet-600/30 font-semibold'
                    : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
                }`}
              >
                <Icon className={`w-5 h-5 ${isActive ? 'text-white' : 'text-slate-400'}`} />
                {item.name}
              </NavLink>
            );
          })}
        </nav>

        {/* System Status Footer */}
        <div className="p-4 border-t border-slate-800/80 bg-slate-950/40">
          <div className="flex items-center justify-between text-xs mb-1.5">
            <span className="text-slate-400">AI Core:</span>
            <span className="inline-flex items-center gap-1.5 font-medium text-emerald-400">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
              {health.gemini_api_configured ? 'Live Gemini' : 'Demo Mode'}
            </span>
          </div>
          <p className="text-[11px] text-slate-400 truncate">
            Model: {health.active_model}
          </p>
          <a
            href="http://localhost:8000/docs"
            target="_blank"
            rel="noreferrer"
            className="mt-3 flex items-center justify-center gap-1 text-[11px] text-violet-300 hover:text-violet-200 py-1 px-2 rounded bg-slate-800/80 border border-slate-700/60 transition"
          >
            <span>OpenAPI Docs</span>
            <ExternalLink className="w-3 h-3" />
          </a>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Top Header (Mobile only navigation toggle) */}
        <header className="md:hidden h-14 bg-white border-b border-slate-200/80 flex items-center justify-between px-4 z-10">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="p-2 rounded-lg text-slate-600 hover:bg-slate-100"
            >
              {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
            <span className="font-bold text-sm text-slate-800">Cognivora AI</span>
          </div>
        </header>

        {/* Mobile Navigation Drawer */}
        {mobileMenuOpen && (
          <div className="md:hidden bg-slate-900 border-b border-slate-800 p-4 space-y-2 z-20">
            {navigation.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname === item.href;
              return (
                <NavLink
                  key={item.name}
                  to={item.href}
                  onClick={() => setMobileMenuOpen(false)}
                  className={`flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium ${
                    isActive
                      ? 'bg-violet-600 text-white'
                      : 'text-slate-300 hover:bg-slate-800'
                  }`}
                >
                  <Icon className="w-5 h-5" />
                  {item.name}
                </NavLink>
              );
            })}
          </div>
        )}

        {/* Dynamic Page Outlet */}
        <main className="flex-1 overflow-y-auto p-4 sm:p-6 lg:p-8 bg-slate-50/70">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
