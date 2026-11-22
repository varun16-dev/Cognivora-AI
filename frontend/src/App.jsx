import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import Documents from './pages/Documents';
import StudyChat from './pages/StudyChat';
import QuizGenerator from './pages/QuizGenerator';
import Flashcards from './pages/Flashcards';
import Summaries from './pages/Summaries';
import AudioLearning from './pages/AudioLearning';
import Analytics from './pages/Analytics';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="documents" element={<Documents />} />
          <Route path="chat" element={<StudyChat />} />
          <Route path="quiz" element={<QuizGenerator />} />
          <Route path="flashcards" element={<Flashcards />} />
          <Route path="summaries" element={<Summaries />} />
          <Route path="audio" element={<AudioLearning />} />
          <Route path="analytics" element={<Analytics />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
