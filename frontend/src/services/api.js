/**
 * Centralized API service client for Cognivora AI backend.
 * Provides resilient network calls, error handling, and JSON decoding.
 */

const API_BASE = "/api";

async function request(endpoint, options = {}) {
  const url = `${API_BASE}${endpoint}`;
  const headers = options.headers || {};

  if (!(options.body instanceof FormData)) {
    headers["Content-Type"] = "application/json";
  }

  try {
    const res = await fetch(url, {
      ...options,
      headers,
    });

    if (!res.ok) {
      let errorMsg = `Server error: ${res.status} ${res.statusText}`;
      try {
        const errorData = await res.json();
        if (errorData.detail) {
          errorMsg = Array.isArray(errorData.detail)
            ? errorData.detail.map((d) => d.msg).join(", ")
            : errorData.detail;
        }
      } catch (e) {
        // Fallback to text
      }
      throw new Error(errorMsg);
    }

    return await res.json();
  } catch (err) {
    console.error(`[API Error] ${endpoint}:`, err);
    throw err;
  }
}

export const api = {
  // System Health
  getHealth: () => request("/health"),

  // Documents
  getDocuments: () => request("/documents"),
  uploadDocument: (formData) =>
    request("/documents/upload", {
      method: "POST",
      body: formData,
    }),
  getDocumentHierarchy: (id) => request(`/documents/${id}/hierarchy`),
  deleteDocument: (id) =>
    request(`/documents/${id}`, {
      method: "DELETE",
    }),

  // Agent Chat
  sendChatMessage: (payload) =>
    request("/agent/chat", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  getAgentLogs: () => request("/agent/logs"),

  // Quizzes
  generateQuiz: (payload) =>
    request("/quiz/generate", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  submitQuiz: (payload) =>
    request("/quiz/submit", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  getQuiz: (id) => request(`/quiz/${id}`),

  // Flashcards
  generateFlashcards: (payload) =>
    request("/flashcards/generate", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  getFlashcardDecks: () => request("/flashcards/list"),

  // Summaries
  generateSummary: (payload) =>
    request("/summary/generate", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  getSummaries: () => request("/summary/list"),

  // Analytics
  getAnalyticsDashboard: () => request("/analytics/dashboard"),
};
