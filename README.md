# Finance MCP

Finance MCP is a modular, production-grade platform for real-time financial data retrieval, caching, and AI agent integration. It features a FastAPI backend and a premium dual-mode React frontend that supports both direct market search and conversational AI (Gemini LLM) interactions.

## Features

- **Dual-Mode Interface**: Seamlessly switch between Search and AI Agent modes.
- **Real-Time Data**: Live stock and crypto quotes via Alpha Vantage, Finnhub, and Binance.
- **AI Agent Mode**: Natural language chat interface powered by Google Gemini with function calling capabilities.
- **Search Mode**: Direct quote lookup with live auto-refresh (5s interval) and day range visualization.
- **Indian Market Support**: Automatic currency conversion to INR (₹) for all prices (1$ = ₹89.94).
- **Advanced Caching**: Redis hot cache and Qdrant semantic cache for low-latency responses.
- **Data Lineage**: Neo4j integration for tracking data provenance.
- **Premium UI**: Modern, Apple-inspired design with smooth transitions and professional aesthetics.

## Architecture

```
User (Web/Agent/LLM)
   │
   ├──> React Frontend (Search & Chat Modes)
   │
   └──> MCP Server (FastAPI)
       ├── Redis (Hot Cache)
       ├── Qdrant (Semantic Cache)
       ├── Neo4j (Graph Lineage)
       └── Connectors: Alpha Vantage, Finnhub, Binance
```

## Getting Started

### Prerequisites

- Docker & Docker Compose
- Python 3.11+
- Node.js 18+ (for frontend)
- API Keys:
  - [Alpha Vantage](https://www.alphavantage.co/support/#api-key) (Stocks)
  - [Finnhub](https://finnhub.io/register) (Stocks)
  - [Google AI Studio](https://aistudio.google.com/) (Gemini API for Agent Mode)

### Installation

1.  **Clone and Configure**

    ```bash
    git clone https://github.com/Anurag7010/finance-mcp.git
    cd finance-mcp
    cp infra/env.sample .env
    ```

    Edit `.env` and add your API keys:

    ```env
    ALPHA_VANTAGE_API_KEY=your_key
    FINNHUB_API_KEY=your_key
    GEMINI_API_KEY=your_key
    MCP_API_KEY=your_secure_backend_key
    ```

2.  **Start Backend Services (Docker)**

    ```bash
    cd infra
    docker-compose up -d --build
    ```

    This launches Redis, Qdrant, Neo4j, and the MCP Server (FastAPI).

3.  **Start Frontend**

    ```bash
    cd ../frontend
    npm install
    npm start
    ```

    Visit http://localhost:3000

## Usage Guide

### Search Mode

- **Instant Quotes**: Enter symbols like `AAPL`, `TSLA`, or `BTCUSDT`.
- **Live Mode**: Toggle to enable 5-second auto-refresh for real-time tracking.
- **Visuals**: View price position within the day's high/low range.
- **History**: Recent queries are saved locally in your browser.

### AI Agent Mode

- **Conversational**: Ask questions like "What is the price of Apple?" or "Compare Bitcoin and Ethereum".
- **Smart Retrieval**: The agent intelligently calls backend tools to fetch real-time data only when needed.
- **Context Aware**: Maintains conversation history for follow-up questions.

### CLI Agent

You can also run the agent directly in the terminal:

```bash
python examples/gemini_agent.py
```

## Security

- **API Key Authentication**: All sensitive endpoints (`/invoke`, `/chat`, `/subscribe`) are protected by an `X-API-Key` header.
- **Environment Variables**: API keys are managed via `.env` and never exposed to the client-side code (except the backend access key).
- **CORS**: Configured to allow secure communication between the React frontend and FastAPI backend.

## Project Structure

```
finance-mcp/
├── mcp_server/         # FastAPI backend & MCP implementation
├── connectors/         # Data source integrations (Alpha Vantage, Binance, etc.)
├── cache/              # Redis & Qdrant client wrappers
├── graph/              # Neo4j lineage tracking
├── agents/             # Gemini agent logic
├── frontend/           # React + TypeScript application
├── infra/              # Docker composition & environment config
└── tests/              # Pytest suite
```

## License

This project is licensed under the MIT License. See `LICENSE` for details.
