# Finance MCP Usage Guide

## Overview

Finance MCP provides two distinct modes for accessing real-time financial market data:

1. **Search Mode**: Direct, manual stock and crypto quote lookups
2. **AI Agent Mode**: Conversational interface powered by Google Gemini

## Search Mode

### Features

- **Instant Quotes**: Enter any stock symbol (AAPL, MSFT, GOOGL) or crypto pair (BTCUSDT, ETHUSDT)
- **Live Mode**: Toggle auto-refresh every 5 seconds to track prices in real-time
- **Day Range Visualizer**: Visual progress bar showing where current price sits within the day's high/low range
- **Price History**: Persistent history of your last 20 queries (saved to browser localStorage)
- **Multi-Currency Display**: All prices shown in Indian Rupees (₹) with 1$ = ₹89.94 conversion

### Usage

1. Select "Search" tab at the top
2. Enter a stock symbol (e.g., TSLA) in the search box
3. Click "Get Quote" or press Enter
4. View detailed quote information including:
   - Current price in ₹
   - Day's high, low, open, and previous close
   - Visual day range indicator
   - Data source and cache status
5. Toggle "Live Mode" for automatic updates
6. Scroll down to view your quote history

### Supported Symbols

- **US Stocks**: AAPL, MSFT, GOOGL, AMZN, TSLA, etc.
- **Crypto**: BTCUSDT, ETHUSDT, BNBUSDT, ADAUSDT, etc.
- **Indian Stocks** (via Alpha Vantage): RELIANCE.BSE, TCS.BSE, INFY.NSE, etc.

## AI Agent Mode

### Features

- **Natural Language Queries**: Ask questions in plain English
- **Real-Time Data**: AI automatically fetches latest market data using MCP tools
- **Conversational Context**: Multi-turn conversations with memory
- **Function Calling**: Gemini intelligently decides when to call stock quote APIs
- **Professional Interface**: Clean message bubbles, typing indicators, and smooth scrolling

### Usage

1. Select "AI Agent" tab at the top
2. Type your question in the chat input (examples below)
3. Press Enter or click Send
4. Wait for AI response with real-time data
5. Continue the conversation naturally

### Example Queries

**Single Stock Queries:**

- "What's the current price of Apple stock?"
- "How is Tesla performing today?"
- "Get me the latest quote for Microsoft"

**Crypto Queries:**

- "What's Bitcoin's price right now?"
- "How much is Ethereum worth?"
- "Show me the current price of Cardano"

**Comparative Queries:**

- "Compare Apple and Microsoft stock prices"
- "Which is doing better today, Tesla or Nio?"
- "Bitcoin vs Ethereum price comparison"

**Market Analysis:**

- "Is Apple stock up or down today?"
- "What's the day range for Tesla?"
- "Has Bitcoin hit a new high today?"

### How It Works

1. Your message is sent to the FastAPI backend `/chat` endpoint
2. Backend forwards to Google Gemini API with tool definitions
3. Gemini analyzes your query and decides if it needs market data
4. If needed, Gemini calls `get_stock_quote` function
5. Backend executes the MCP tool and returns data to Gemini
6. Gemini formats a natural language response with the data
7. Response is displayed in the chat interface

All prices are automatically converted to INR (₹) before display.

## Mode Switching

Switch between Search and AI Agent modes anytime using the tabs at the top of the page. Your quote history in Search mode persists even when you switch to AI Agent mode and back.

## API Keys Required

- **ALPHA_VANTAGE_API_KEY**: For stock data (free tier: 5 calls/min)
- **FINNHUB_API_KEY**: For stock data (free tier: 60 calls/min)
- **GEMINI_API_KEY**: For AI Agent mode (Google AI Studio, free tier)
- **REACT_APP_API_KEY**: Frontend authentication (set in `.env`)

Without GEMINI_API_KEY, Search mode will work but AI Agent mode will return an error.

## Tips & Best Practices

### Search Mode

- Use the Live Mode toggle for stocks you're actively monitoring
- View the day range visualizer to understand price volatility
- Check the "Cache Hit" indicator - cached responses are faster
- History is saved in your browser - clear localStorage to reset

### AI Agent Mode

- Be specific with stock symbols or company names
- Ask follow-up questions to drill deeper into data
- Request comparisons for side-by-side analysis
- Gemini understands context from previous messages in the session

## Troubleshooting

### Search Mode Issues

- **"Error fetching quote"**: Check if API keys are configured in `.env`
- **Rate limit errors**: Switch data sources or wait a minute
- **No data for symbol**: Verify symbol format (e.g., BTCUSDT not BTC)

### AI Agent Mode Issues

- **"Gemini API key not configured"**: Add GEMINI_API_KEY to backend `.env`
- **"Network error"**: Ensure backend is running on http://localhost:8000
- **Slow responses**: Gemini API may take 2-5 seconds for complex queries
- **No data in response**: AI might not have called the tool - rephrase your query

## Currency Display

All prices are displayed in Indian Rupees (₹) using the conversion rate of **₹89.94 per USD**. This applies to both Search and AI Agent modes. The backend performs USD-to-INR conversion automatically.

## Data Sources

- **Alpha Vantage**: US stocks, Indian stocks (NSE/BSE)
- **Finnhub**: US stocks, real-time quotes
- **Binance**: Cryptocurrency pairs (WebSocket for live data)

The system intelligently routes requests based on symbol format and availability.

## Privacy & Storage

- **Quote History**: Stored locally in your browser (localStorage)
- **Chat Messages**: Not persisted - cleared on page refresh
- **API Keys**: Stored server-side only, never exposed to frontend
- **No user authentication**: Demo mode uses dev API key

For production use, implement proper authentication and user management.
