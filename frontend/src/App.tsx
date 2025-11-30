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
                <p className="text-sm text-slate-400">
                  Real-Time Market Data Platform
                </p>
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
          <div className="grid md:grid-cols-3 gap-6">
            <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
              <div className="flex items-center gap-3 mb-3">
                <div className="p-2 bg-green-600/20 rounded-lg">
                  <TrendingUp className="w-5 h-5 text-green-400" />
                </div>
                <h3 className="text-lg font-semibold text-white">
                  Real-Time Data
                </h3>
              </div>
              <p className="text-slate-400 text-sm">
                Access live stock and cryptocurrency prices from multiple data
                providers including Finnhub, Alpha Vantage, and Binance.
              </p>
            </div>

            <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
              <div className="flex items-center gap-3 mb-3">
                <div className="p-2 bg-blue-600/20 rounded-lg">
                  <svg
                    className="w-5 h-5 text-blue-400"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M13 10V3L4 14h7v7l9-11h-7z"
                    />
                  </svg>
                </div>
                <h3 className="text-lg font-semibold text-white">
                  Smart Caching
                </h3>
              </div>
              <p className="text-slate-400 text-sm">
                Multi-layer caching with Redis and Qdrant ensures blazing-fast
                responses and reduces API costs.
              </p>
            </div>

            <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
              <div className="flex items-center gap-3 mb-3">
                <div className="p-2 bg-purple-600/20 rounded-lg">
                  <svg
                    className="w-5 h-5 text-purple-400"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"
                    />
                  </svg>
                </div>
                <h3 className="text-lg font-semibold text-white">
                  MCP Protocol
                </h3>
              </div>
              <p className="text-slate-400 text-sm">
                Built on the Model Context Protocol for seamless AI agent
                integration with standardized tool definitions.
              </p>
            </div>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="mt-12 py-6 border-t border-slate-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <p className="text-center text-slate-500 text-sm">
            Built with React, TypeScript, Tailwind CSS, and FastAPI • Powered by
            MCP
          </p>
        </div>
      </footer>
    </div>
  );
}

export default App;
