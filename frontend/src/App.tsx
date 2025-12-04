import React, { useState, useEffect } from "react";
import { TrendingUp, Github, Search, MessageSquare } from "lucide-react";
import QuoteCard from "./components/QuoteCard";
import StatusBar from "./components/StatusBar";
import PriceHistory from "./components/PriceHistory";
import ChatInterface from "./components/ChatInterface";
import { QuoteData } from "./services/api";

const STORAGE_KEY = "finance_mcp_quote_history";

type AppMode = "search" | "agent";

function App() {
  const [mode, setMode] = useState<AppMode>("search");

  // Load history from localStorage on mount
  const [quoteHistory, setQuoteHistory] = useState<QuoteData[]>(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      return saved ? JSON.parse(saved) : [];
    } catch {
      return [];
    }
  });

  // Save history to localStorage whenever it changes
  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(quoteHistory));
    } catch (error) {
      console.error("Failed to save history:", error);
    }
  }, [quoteHistory]);

  const handleQuoteUpdate = (quote: QuoteData) => {
    setQuoteHistory((prev) => [...prev, quote].slice(-20)); // Keep last 20 queries
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      {/* Header */}
      <header className="bg-slate-900/80 backdrop-blur-sm border-b border-slate-700 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-primary-600 rounded-lg">
                <TrendingUp className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-white">Finance MCP</h1>
                <p className="text-sm text-slate-400">Real-Time Market Data</p>
              </div>
            </div>
            <a
              href="https://github.com/Anurag7010/finance-mcp"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-lg transition-colors duration-200"
            >
              <Github className="w-5 h-5" />
              <span className="hidden sm:inline">GitHub</span>
            </a>
          </div>
        </div>
      </header>

      {/* Mode Switcher */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-8">
        <div className="inline-flex bg-slate-800 rounded-lg p-1 border border-slate-700">
          <button
            onClick={() => setMode("search")}
            className={`flex items-center gap-2 px-6 py-2.5 rounded-md font-medium transition-all duration-200 ${
              mode === "search"
                ? "bg-primary-600 text-white shadow-lg"
                : "text-slate-400 hover:text-white"
            }`}
          >
            <Search className="w-4 h-4" />
            <span>Search</span>
          </button>
          <button
            onClick={() => setMode("agent")}
            className={`flex items-center gap-2 px-6 py-2.5 rounded-md font-medium transition-all duration-200 ${
              mode === "agent"
                ? "bg-primary-600 text-white shadow-lg"
                : "text-slate-400 hover:text-white"
            }`}
          >
            <MessageSquare className="w-4 h-4" />
            <span>AI Agent</span>
          </button>
        </div>
      </div>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="space-y-6">
          {/* Status Bar */}
          <StatusBar />

          {/* Conditional Rendering based on mode */}
          {mode === "search" ? (
            <>
              {/* Quote Search */}
              <QuoteCard onQuoteUpdate={handleQuoteUpdate} />

              {/* Price History */}
              <PriceHistory quotes={quoteHistory} />
            </>
          ) : (
            <>
              {/* AI Chat Interface */}
              <ChatInterface />
            </>
          )}
        </div>
      </main>

      {/* Footer */}
      <footer className="mt-12 py-6 border-t border-slate-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <p className="text-center text-slate-500 text-sm">
            Built with React, TypeScript, Tailwind CSS, and FastAPI
          </p>
        </div>
      </footer>
    </div>
  );
}

export default App;
