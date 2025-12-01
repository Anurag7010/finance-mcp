# Finance MCP

Finance MCP is a modular, production-grade platform for real-time financial data retrieval, caching, and AI agent integration. It features a FastAPI backend, React frontend, and supports both direct search and conversational (Gemini LLM) modes.

## Features

- Real-time and historical price data for stocks and crypto (Alpha Vantage, Finnhub, Binance)
- Redis hot cache and Qdrant semantic cache for low-latency and intelligent response
- Neo4j graph lineage for data provenance
- REST API and WebSocket support
- Modern React + TypeScript + Tailwind frontend
- Gemini LLM agent integration (Google AI Studio, free tier)

## Architecture

```
User (Web/Agent/LLM)
   │
   ├──> React Frontend (search & chat modes)
   │
   └──> MCP Server (FastAPI)
       ├── Redis (hot cache)
       ├── Qdrant (semantic cache)
       ├── Neo4j (graph lineage)
       └── Connectors: Alpha Vantage, Finnhub, Binance
```

## Project Structure

```
finance-mcp/
├── mcp_server/         # FastAPI backend
├── connectors/         # Data source connectors
├── cache/              # Redis & Qdrant clients
├── graph/              # Neo4j integration
├── agents/             # Agent logic
├── examples/           # Demo agents (Gemini, etc.)
├── frontend/           # React + TypeScript UI
├── infra/              # Docker, env, deployment
├── tests/              # Test suite
├── openapi.yaml        # API spec
├── requirements.txt    # Python dependencies
└── LICENSE
```

docker-compose up -d

## Getting Started

### Prerequisites

- Docker & Docker Compose
- Python 3.11+
- Node.js 18+ (for frontend)
- Free API keys: [Alpha Vantage](https://www.alphavantage.co/support/#api-key), [Finnhub](https://finnhub.io/register)

### 1. Clone and Configure

```bash
git clone https://github.com/Anurag7010/finance-mcp.git
cd finance-mcp
cp infra/env.sample .env
# Edit .env and add API keys for Finnhub, AlphaVantage and Gemini
```

### 2. Start All Services (Docker)

```bash
cd infra
docker-compose up -d
```

This launches Redis, Qdrant, Neo4j, and the MCP server.

### 3. Start the Frontend

```bash
cd ../frontend
npm install
npm start
```

Visit http://localhost:3000

### 4. Verify Backend

```bash
curl http://localhost:8000/health
curl http://localhost:8000/.well-known/mcp
curl http://localhost:8000/capabilities
```

### 5. Test API Endpoints

```bash
# Get latest stock quote
curl -X POST http://localhost:8000/invoke \
  -H "Content-Type: application/json" \
  -d '{"tool_name": "quote.latest", "arguments": {"symbol": "AAPL"}}'

# Subscribe to real-time crypto stream
curl -X POST http://localhost:8000/subscribe \
  -H "Content-Type: application/json" \
  -d '{"symbol": "BTCUSDT", "channel": "trades"}'
```

docker run -d --name redis -p 6379:6379 redis:7-alpine
docker run -d --name qdrant -p 6333:6333 qdrant/qdrant:latest
docker run -d --name neo4j -p 7474:7474 -p 7687:7687 \

## Local Development (No Docker)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
# Start Redis, Qdrant, Neo4j manually (see infra/docker-compose.yml for images/ports)
uvicorn mcp_server.server:app --reload --port 8000
```

### Usage

```bash
cd frontend
npm install
npm start
# Open http://localhost:3000
```

### Run the Gemini Agent

```bash
python examples/gemini_agent.py
# Or: python examples/gemini_agent.py --demo
```

Type questions like "What is the price of Bitcoin?" and the agent will call MCP tools automatically.

## Data Providers

- **Alpha Vantage**: Stocks, REST, 5 calls/min (free tier)
- **Finnhub**: Stocks, REST, 60 calls/min (free tier)
- **Binance**: Crypto, WebSocket, unlimited

## Testing

```bash
pytest tests/ -v
```

## Environment Variables

See `infra/env.sample` for all options. Key variables:

| Variable              | Description           |
| --------------------- | --------------------- |
| REDIS_HOST            | Redis hostname        |
| QDRANT_HOST           | Qdrant hostname       |
| NEO4J_URI             | Neo4j connection URI  |
| ALPHA_VANTAGE_API_KEY | Alpha Vantage API key |
| FINNHUB_API_KEY       | Finnhub API key       |
| GEMINI_API_KEY        | Google Gemini API key |

## API Documentation

- OpenAPI: `openapi.yaml`
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

docker ps | grep redis
docker logs finance-mcp-neo4j

## Troubleshooting

- Ensure all containers are running: `docker-compose ps`
- Check `.env` for correct API keys
- Redis: `redis-cli ping` should return PONG
- Qdrant: `curl http://localhost:6333/collections`
- Neo4j: http://localhost:7474 (user: neo4j, pass: password123)
- For rate limits, use Binance for crypto (unlimited)

## License

This project is licensed under the MIT License. See `LICENSE` for details.
