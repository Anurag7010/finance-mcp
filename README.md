# Finance MCP Server

Real-Time Financial Data MCP Integration System with free/open-source tools.

## Overview

This system enables AI agents (LangChain agents) to retrieve and process real-time financial data through an MCP (Model Context Protocol) Server, featuring:

- **Redis Hot Cache**: Fast snapshot caching and stream ingestion
- **Qdrant Semantic Cache**: Vector-based similarity search for agent responses
- **Neo4j Graph Lineage**: Data lineage and relationship tracking
- **Free Data Providers**: Alpha Vantage, Finnhub, Binance WebSocket

## Architecture

```
LangChain Agent
    → MCP Server
        → Semantic Cache (Qdrant)
        → Redis Hot Cache
        → Connectors
            → Alpha Vantage (REST)
            → Finnhub (REST)
            → Binance (WebSocket)
        → Neo4j (lineage)
```

## Project Structure

```
finance-mcp/
├── mcp_server/           # MCP Server implementation
│   ├── server.py         # FastAPI application
│   ├── config.py         # Configuration management
│   ├── schemas.py        # Pydantic schemas
│   ├── capabilities.json # MCP capabilities definition
│   ├── invoke_handlers/  # Tool handlers
│   │   ├── quote_latest.py
│   │   └── quote_stream.py
│   └── utils/
│       ├── logging.py
│       └── validation.py
├── connectors/           # Data source connectors
│   ├── alpha_vantage.py  # Alpha Vantage REST
│   ├── finnhub.py        # Finnhub REST
│   └── binance_ws.py     # Binance WebSocket
├── cache/                # Caching layer
│   ├── redis_client.py   # Redis hot cache
│   └── qdrant_client.py  # Semantic cache
├── graph/                # Graph database
│   ├── neo4j_client.py   # Neo4j operations
│   └── lineage_writer.py # Lineage tracking
├── agents/               # LangChain agent
│   └── agent.py
├── tests/                # Test suite
├── infra/                # Infrastructure
│   ├── docker-compose.yml
│   ├── Dockerfile
│   └── env.sample
├── openapi.yaml          # API specification
└── requirements.txt
```

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.11+
- API Keys (free tier):
  - [Alpha Vantage](https://www.alphavantage.co/support/#api-key)
  - [Finnhub](https://finnhub.io/register)

### 1. Clone and Configure

```bash
cd finance-mcp

# Copy environment template
cp infra/env.sample .env

# Edit .env with your API keys
nano .env
```

### 2. Start Infrastructure

```bash
cd infra
docker-compose up -d
```

This starts:

- Redis (port 6379)
- Qdrant (port 6333)
- Neo4j (port 7474, 7687)
- MCP Server (port 8000)

### 3. Verify Services

```bash
# Check health
curl http://localhost:8000/health

# View MCP metadata
curl http://localhost:8000/.well-known/mcp

# Get capabilities
curl http://localhost:8000/capabilities
```

### 4. Test the API

```bash
# Get latest stock quote
curl -X POST http://localhost:8000/invoke \
  -H "Content-Type: application/json" \
  -d '{
    "tool_name": "quote.latest",
    "arguments": {"symbol": "AAPL", "maxAgeSec": 60}
  }'

# Get crypto quote
curl -X POST http://localhost:8000/invoke \
  -H "Content-Type: application/json" \
  -d '{
    "tool_name": "quote.latest",
    "arguments": {"symbol": "BTCUSDT"}
  }'

# Subscribe to real-time stream
curl -X POST http://localhost:8000/subscribe \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "BTCUSDT",
    "channel": "trades"
  }'
```

## Local Development (Without Docker)

### 1. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # macOS/Linux
# or: venv\Scripts\activate  # Windows
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Start External Services

```bash
# Redis
docker run -d --name redis -p 6379:6379 redis:7-alpine

# Qdrant
docker run -d --name qdrant -p 6333:6333 qdrant/qdrant:latest

# Neo4j
docker run -d --name neo4j -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/password123 \
  neo4j:5-community
```

### 4. Run MCP Server

```bash
# Update .env for localhost connections
export REDIS_HOST=localhost
export QDRANT_HOST=localhost
export NEO4J_URI=bolt://localhost:7687

# Start server
uvicorn mcp_server.server:app --reload --port 8000
```

### 5. Run Agent Demo

```bash
python -m agents.agent
```

## MCP Tools

### quote.latest

Get the latest price quote for a financial instrument.

**Request:**

```json
{
  "tool_name": "quote.latest",
  "arguments": {
    "symbol": "AAPL",
    "exchange": "NASDAQ",
    "maxAgeSec": 60
  },
  "agent_id": "agent_001",
  "query_text": "What is the current price of Apple stock?"
}
```

**Response:**

```json
{
  "success": true,
  "data": {
    "symbol": "AAPL",
    "price": 150.5,
    "timestamp": "2025-11-29T12:00:00Z",
    "data_source": "finnhub",
    "cache_hit": false,
    "latency_ms": 245.5,
    "volume": 1500000,
    "high": 152.0,
    "low": 149.0
  },
  "cache_hit": false,
  "data_source": "finnhub",
  "latency_ms": 245.5
}
```

### quote.stream

Subscribe to real-time price stream (crypto only via Binance).

**Request:**

```json
{
  "tool_name": "quote.stream",
  "arguments": {
    "symbol": "BTCUSDT",
    "channel": "trades"
  }
}
```

**Response:**

```json
{
  "success": true,
  "data": {
    "subscription_id": "sub_abc12345",
    "status": "subscribed",
    "symbol": "BTCUSDT",
    "channel": "trades"
  }
}
```

## Caching Architecture

### Redis Hot Cache

- **Snapshots**: `hash:snapshot:{symbol}` - Latest price data
- **Streams**: `stream:{symbol}` - Real-time tick stream

Cache policy:

1. Check Redis snapshot age
2. If fresh (< maxAgeSec) → return cached
3. Else → fetch from connector → update cache → return

### Qdrant Semantic Cache

- **Collection**: `AgentResponse`
- **Embedding**: `all-MiniLM-L6-v2` (384 dimensions)
- **Threshold**: 0.86 similarity
- **Recency**: 5 minutes

Semantic cache policy:

1. Embed query text
2. Search for similar queries within recency window
3. If similarity >= threshold → return cached response
4. Else → fetch new data → store response

## Graph Lineage (Neo4j)

### Node Types

- `API` - Data provider
- `Endpoint` - API endpoint
- `Instrument` - Financial instrument
- `Event` - Price/trade event
- `Agent` - LangChain agent
- `Query` - User query

### Edge Types

- `PROVIDES` (API → Endpoint)
- `CALLS` (Agent → API) with latency, timestamp, response_code
- `EMITS` (Endpoint → Event)
- `ABOUT` (Event → Instrument)
- `DEPENDS_ON` (Indicator → Instrument)

### Access Neo4j Browser

Open http://localhost:7474 and login with:

- Username: `neo4j`
- Password: `password123`

Example queries:

```cypher
// View all agent calls
MATCH (ag:Agent)-[r:CALLS]->(a:API)
RETURN ag, r, a

// View instrument events
MATCH (ev:Event)-[:ABOUT]->(i:Instrument {symbol: 'BTCUSDT'})
RETURN ev ORDER BY ev.timestamp DESC LIMIT 10
```

## Data Providers

### Alpha Vantage

- **Type**: REST API
- **Rate Limit**: 5 calls/minute (free tier)
- **Use Case**: Stock quotes, fallback source
- **Docs**: https://www.alphavantage.co/documentation/

### Finnhub

- **Type**: REST API
- **Rate Limit**: 60 calls/minute (free tier)
- **Use Case**: Primary stock quote source
- **Docs**: https://finnhub.io/docs/api

### Binance

- **Type**: WebSocket
- **Rate Limit**: Unlimited
- **Use Case**: Real-time crypto streaming
- **Stream**: `wss://stream.binance.com:9443/ws/{symbol}@trade`
- **Docs**: https://binance-docs.github.io/apidocs/spot/en/

## Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_mcp_invoke.py -v

# Run with coverage
pytest tests/ --cov=mcp_server --cov=connectors --cov=cache
```

## Environment Variables

| Variable                   | Description           | Default                 |
| -------------------------- | --------------------- | ----------------------- |
| `REDIS_HOST`               | Redis hostname        | `localhost`             |
| `REDIS_PORT`               | Redis port            | `6379`                  |
| `QDRANT_HOST`              | Qdrant hostname       | `localhost`             |
| `QDRANT_PORT`              | Qdrant port           | `6333`                  |
| `NEO4J_URI`                | Neo4j connection URI  | `bolt://localhost:7687` |
| `NEO4J_USER`               | Neo4j username        | `neo4j`                 |
| `NEO4J_PASSWORD`           | Neo4j password        | `password123`           |
| `ALPHA_VANTAGE_API_KEY`    | Alpha Vantage API key | `demo`                  |
| `FINNHUB_API_KEY`          | Finnhub API key       | `demo`                  |
| `DEFAULT_MAX_AGE_SEC`      | Default cache age     | `60`                    |
| `SEMANTIC_CACHE_THRESHOLD` | Similarity threshold  | `0.86`                  |
| `LOG_LEVEL`                | Logging level         | `INFO`                  |

## API Documentation

- **OpenAPI Spec**: `openapi.yaml`
- **Swagger UI**: http://localhost:8000/docs (when running)
- **ReDoc**: http://localhost:8000/redoc (when running)

## Troubleshooting

### Redis Connection Failed

```bash
# Check Redis is running
docker ps | grep redis

# Test connection
redis-cli ping
```

### Qdrant Connection Failed

```bash
# Check Qdrant is running
curl http://localhost:6333/

# Check collections
curl http://localhost:6333/collections
```

### Neo4j Connection Failed

```bash
# Check Neo4j is running
curl http://localhost:7474/

# Check logs
docker logs finance-mcp-neo4j
```

### Rate Limit Errors

- Alpha Vantage: Wait 60 seconds between calls
- Finnhub: Wait 1 second between calls
- Use crypto symbols (e.g., BTCUSDT) with Binance for unlimited real-time data

## License

MIT License
