"""
LangChain Agent for Finance MCP Integration
"""
import re
import json
import httpx
from typing import Optional, Dict, Any, List
from datetime import datetime

from langchain.agents import AgentExecutor, create_react_agent
from langchain.tools import Tool, StructuredTool
from langchain.prompts import PromptTemplate
from langchain_core.language_models.base import BaseLanguageModel

from mcp_server.utils.logging import get_logger

logger = get_logger(__name__)


class MCPFinanceAgent:
    """
    LangChain agent that interacts with Finance MCP Server
    
    Capabilities:
    - Reads MCP /capabilities
    - Determines tool by rule matching
    - Calls MCP /invoke
    - Handles fallback on errors
    - Outputs financial insights
    """
    
    MCP_BASE_URL = "http://localhost:8000"
    
    def __init__(self, agent_id: str = "langchain_agent_001", llm: Optional[BaseLanguageModel] = None):
        self.agent_id = agent_id
        self._client = httpx.Client(timeout=30.0)
        self._capabilities: Optional[Dict] = None
        self._llm = llm
        
    async def initialize(self) -> bool:
        """Initialize the agent by fetching MCP capabilities"""
        try:
            response = self._client.get(f"{self.MCP_BASE_URL}/capabilities")
            response.raise_for_status()
            self._capabilities = response.json()
            logger.info("agent_initialized", capabilities=list(t["name"] for t in self._capabilities.get("tools", [])))
            return True
        except Exception as e:
            logger.error("agent_init_failed", error=str(e))
            return False
    
    def get_available_tools(self) -> List[str]:
        """Get list of available MCP tools"""
        if not self._capabilities:
            return []
        return [t["name"] for t in self._capabilities.get("tools", [])]
    
    def determine_tool(self, query: str) -> str:
        """
        Determine which MCP tool to use based on query
        
        Rules:
        - "real-time", "stream", "live" -> quote.stream
        - "last X minutes", "latest", "current", "price" -> quote.latest
        """
        query_lower = query.lower()
        
        # Stream indicators
        stream_patterns = ["real-time", "realtime", "stream", "live", "continuous", "subscribe"]
        for pattern in stream_patterns:
            if pattern in query_lower:
                return "quote.stream"
        
        # Latest indicators (default)
        return "quote.latest"
    
    def extract_symbol(self, query: str) -> Optional[str]:
        """Extract symbol from query"""
        # Common patterns
        patterns = [
            r'\b([A-Z]{1,5})\b',  # Stock symbols like AAPL, MSFT
            r'\b([A-Z]{2,}USDT?)\b',  # Crypto like BTCUSDT, ETHUSDT
            r'symbol[:\s]+([A-Za-z0-9]+)',  # Explicit symbol mention
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, query.upper())
            if matches:
                # Filter out common words
                common_words = {"THE", "FOR", "AND", "GET", "SHOW", "WHAT", "PRICE", "OF", "IS"}
                for match in matches:
                    if match not in common_words:
                        return match
        
        return None
    
    def extract_channel(self, query: str) -> str:
        """Extract channel type from query"""
        query_lower = query.lower()
        if "quote" in query_lower or "bid" in query_lower or "ask" in query_lower:
            return "quotes"
        return "trades"
    
    async def invoke_mcp_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        query_text: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Invoke an MCP tool
        """
        try:
            payload = {
                "tool_name": tool_name,
                "arguments": arguments,
                "agent_id": self.agent_id,
                "query_text": query_text
            }
            
            logger.info("mcp_invoke", tool=tool_name, args=arguments)
            
            response = self._client.post(
                f"{self.MCP_BASE_URL}/invoke",
                json=payload
            )
            
            result = response.json()
            
            if result.get("success"):
                logger.info("mcp_invoke_success", tool=tool_name)
            else:
                logger.warning("mcp_invoke_failed", tool=tool_name, error=result.get("error"))
            
            return result
            
        except Exception as e:
            logger.error("mcp_invoke_error", error=str(e))
            return {"success": False, "error": str(e)}
    
    async def process_query(self, query: str) -> Dict[str, Any]:
        """
        Process a user query end-to-end
        
        1. Parse query
        2. Determine tool
        3. Extract parameters
        4. Invoke MCP
        5. Generate insight
        """
        logger.info("processing_query", query=query[:100])
        
        # Determine tool
        tool_name = self.determine_tool(query)
        
        # Extract symbol
        symbol = self.extract_symbol(query)
        if not symbol:
            return {
                "success": False,
                "error": "Could not extract symbol from query",
                "hint": "Please include a valid ticker symbol (e.g., AAPL, BTCUSDT)"
            }
        
        # Build arguments
        if tool_name == "quote.latest":
            arguments = {
                "symbol": symbol,
                "maxAgeSec": 60
            }
        else:  # quote.stream
            arguments = {
                "symbol": symbol,
                "channel": self.extract_channel(query)
            }
        
        # Invoke MCP
        result = await self.invoke_mcp_tool(tool_name, arguments, query)
        
        if not result.get("success"):
            return result
        
        # Generate insight
        insight = self._generate_insight(result.get("data", {}), symbol)
        
        return {
            "success": True,
            "tool_used": tool_name,
            "symbol": symbol,
            "data": result.get("data"),
            "insight": insight,
            "cache_hit": result.get("cache_hit", False),
            "data_source": result.get("data_source"),
            "latency_ms": result.get("latency_ms")
        }
    
    def _generate_insight(self, data: Dict[str, Any], symbol: str) -> str:
        """Generate human-readable insight from data"""
        if not data:
            return f"No data available for {symbol}"
        
        parts = []
        
        # Price info
        price = data.get("price")
        if price:
            parts.append(f"Current price of {symbol}: ${price:,.2f}")
        
        # Price change
        prev_close = data.get("previous_close")
        if price and prev_close and prev_close > 0:
            change = price - prev_close
            change_pct = (change / prev_close) * 100
            direction = "📈" if change >= 0 else "📉"
            parts.append(f"Change: {direction} ${change:+,.2f} ({change_pct:+.2f}%)")
        
        # High/Low
        high = data.get("high")
        low = data.get("low")
        if high and low:
            parts.append(f"Day range: ${low:,.2f} - ${high:,.2f}")
        
        # Volume
        volume = data.get("volume")
        if volume:
            parts.append(f"Volume: {volume:,.0f}")
        
        # Data age
        timestamp = data.get("timestamp")
        if timestamp:
            try:
                dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                age = (datetime.utcnow() - dt.replace(tzinfo=None)).total_seconds()
                if age < 60:
                    parts.append(f"Data age: {age:.1f} seconds")
                else:
                    parts.append(f"Data age: {age/60:.1f} minutes")
            except:
                pass
        
        # Cache info
        cache_hit = data.get("cache_hit")
        source = data.get("data_source")
        parts.append(f"Source: {source} {'(cached)' if cache_hit else '(fresh)'}")
        
        return "\n".join(parts) if parts else f"Data retrieved for {symbol}"
    
    def close(self):
        """Close the HTTP client"""
        self._client.close()


# ==================== LANGCHAIN TOOLS ====================

def create_mcp_tools(agent: MCPFinanceAgent) -> List[Tool]:
    """Create LangChain tools from MCP capabilities"""
    
    async def get_quote_latest(symbol: str) -> str:
        """Get the latest price quote for a financial instrument"""
        result = await agent.invoke_mcp_tool(
            "quote.latest",
            {"symbol": symbol, "maxAgeSec": 60}
        )
        if result.get("success"):
            return json.dumps(result.get("data"), indent=2)
        return f"Error: {result.get('error')}"
    
    async def subscribe_stream(symbol: str, channel: str = "trades") -> str:
        """Subscribe to real-time price stream"""
        result = await agent.invoke_mcp_tool(
            "quote.stream",
            {"symbol": symbol, "channel": channel}
        )
        if result.get("success"):
            return json.dumps(result.get("data"), indent=2)
        return f"Error: {result.get('error')}"
    
    tools = [
        Tool(
            name="quote_latest",
            description="Get the latest price quote for a stock or cryptocurrency. Input should be the ticker symbol (e.g., AAPL, BTCUSDT).",
            func=lambda x: None,
            coroutine=get_quote_latest
        ),
        Tool(
            name="quote_stream",
            description="Subscribe to real-time price stream. Input should be the ticker symbol.",
            func=lambda x: None,
            coroutine=subscribe_stream
        )
    ]
    
    return tools


# ==================== STANDALONE USAGE ====================

async def run_agent_demo():
    """Demo function to show agent usage"""
    agent = MCPFinanceAgent(agent_id="demo_agent")
    
    # Initialize
    print("Initializing agent...")
    if not await agent.initialize():
        print("Failed to initialize agent")
        return
    
    print(f"Available tools: {agent.get_available_tools()}")
    
    # Test queries
    test_queries = [
        "What is the current price of AAPL?",
        "Get me the latest BTCUSDT price",
        "Show me real-time stream for ETHUSDT",
        "What's MSFT trading at?"
    ]
    
    for query in test_queries:
        print(f"\n{'='*50}")
        print(f"Query: {query}")
        print(f"{'='*50}")
        
        result = await agent.process_query(query)
        
        if result.get("success"):
            print(f"\n{result.get('insight')}")
        else:
            print(f"Error: {result.get('error')}")
    
    agent.close()


if __name__ == "__main__":
    import asyncio
    asyncio.run(run_agent_demo())
