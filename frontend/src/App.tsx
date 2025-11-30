import React, { useState } from "react";
import { TrendingUp, Github } from "lucide-react";
import QuoteCard from "./components/QuoteCard";
import StatusBar from "./components/StatusBar";
import PriceHistory from "./components/PriceHistory";
import { QuoteData } from "./services/api";

function App() {
  const [quoteHistory, setQuoteHistory] = useState<QuoteData[]>([]);

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

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="space-y-6">
          {/* Status Bar */}
          <StatusBar />

          {/* Quote Search */}
          <QuoteCard onQuoteUpdate={handleQuoteUpdate} />

          {/* Price History */}
          <PriceHistory quotes={quoteHistory} />

          {/* Info Cards */}
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
