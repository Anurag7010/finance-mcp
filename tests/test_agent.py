"""
Tests for LangChain Finance Agent
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from agents.agent import MCPFinanceAgent


class TestAgentQueryParsing:
    """Tests for query parsing and tool selection"""
    
    @pytest.fixture
    def agent(self):
        """Create agent instance"""
        return MCPFinanceAgent(agent_id="test_agent")
    
    def test_determine_tool_latest(self, agent):
        """Test tool selection for latest price queries"""
        queries = [
            "What is the current price of AAPL?",
            "Get me the latest BTCUSDT price",
            "Show MSFT price",
            "What's GOOGL trading at?"
        ]
        
        for query in queries:
            tool = agent.determine_tool(query)
            assert tool == "quote.latest", f"Failed for query: {query}"
    
    def test_determine_tool_stream(self, agent):
        """Test tool selection for stream queries"""
        queries = [
            "Show me real-time stream for BTCUSDT",
            "Start live feed for ETHUSDT",
            "Subscribe to realtime data",
            "Give me continuous updates"
        ]
        
        for query in queries:
            tool = agent.determine_tool(query)
            assert tool == "quote.stream", f"Failed for query: {query}"
    
    def test_extract_symbol_stocks(self, agent):
        """Test symbol extraction for stocks"""
        test_cases = [
            ("What is AAPL price?", "AAPL"),
            ("Get MSFT quote", "MSFT"),
            ("Show me GOOGL", "GOOGL"),
            ("Tesla stock TSLA", "TSLA")
        ]
        
        for query, expected in test_cases:
            symbol = agent.extract_symbol(query)
            assert symbol == expected, f"Failed for query: {query}, got {symbol}"
    
    def test_extract_symbol_crypto(self, agent):
        """Test symbol extraction for crypto"""
        test_cases = [
            ("What is BTCUSDT trading at?", "BTCUSDT"),
            ("Show ETHUSDT price", "ETHUSDT"),
            ("Get BNBUSDT quote", "BNBUSDT")
        ]
        
        for query, expected in test_cases:
            symbol = agent.extract_symbol(query)
            assert symbol == expected, f"Failed for query: {query}, got {symbol}"
    
    def test_extract_channel(self, agent):
        """Test channel extraction"""
        assert agent.extract_channel("Show trades for BTC") == "trades"
        assert agent.extract_channel("Get quote data") == "quotes"
        assert agent.extract_channel("Bid/ask spread") == "quotes"


class TestAgentMCPInvocation:
    """Tests for MCP tool invocation"""
    
    @pytest.fixture
    def agent(self):
        """Create agent with mocked HTTP client"""
        agent = MCPFinanceAgent(agent_id="test_agent")
        agent._client = MagicMock()
        return agent
    
    @pytest.mark.asyncio
    async def test_invoke_mcp_tool_success(self, agent):
        """Test successful MCP invocation"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "success": True,
            "data": {
                "symbol": "AAPL",
                "price": 150.0
            }
        }
        agent._client.post.return_value = mock_response
        
        result = await agent.invoke_mcp_tool(
            "quote.latest",
            {"symbol": "AAPL"}
        )
        
        assert result["success"] == True
        assert result["data"]["price"] == 150.0
    
    @pytest.mark.asyncio
    async def test_invoke_mcp_tool_failure(self, agent):
        """Test MCP invocation failure handling"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "success": False,
            "error": "Rate limit exceeded"
        }
        agent._client.post.return_value = mock_response
        
        result = await agent.invoke_mcp_tool(
            "quote.latest",
            {"symbol": "AAPL"}
        )
        
        assert result["success"] == False
        assert "Rate limit" in result["error"]


class TestAgentInsightGeneration:
    """Tests for insight generation"""
    
    @pytest.fixture
    def agent(self):
        return MCPFinanceAgent(agent_id="test_agent")
    
    def test_generate_insight_with_price(self, agent):
        """Test insight with price data"""
        data = {
            "symbol": "AAPL",
            "price": 150.50,
            "previous_close": 148.00
        }
        
        insight = agent._generate_insight(data, "AAPL")
        
        assert "AAPL" in insight
        assert "150.50" in insight
        assert "📈" in insight  # Price went up
    
    def test_generate_insight_with_price_decrease(self, agent):
        """Test insight with price decrease"""
        data = {
            "symbol": "AAPL",
            "price": 145.00,
            "previous_close": 148.00
        }
        
        insight = agent._generate_insight(data, "AAPL")
        
        assert "📉" in insight  # Price went down
    
    def test_generate_insight_with_range(self, agent):
        """Test insight with high/low range"""
        data = {
            "symbol": "AAPL",
            "price": 150.00,
            "high": 155.00,
            "low": 145.00
        }
        
        insight = agent._generate_insight(data, "AAPL")
        
        assert "range" in insight.lower()
        assert "145" in insight
        assert "155" in insight
    
    def test_generate_insight_empty_data(self, agent):
        """Test insight with empty data"""
        insight = agent._generate_insight({}, "AAPL")
        
        assert "No data" in insight


class TestAgentFullFlow:
    """Tests for end-to-end query processing"""
    
    @pytest.fixture
    def agent(self):
        """Create agent with mocked HTTP client"""
        agent = MCPFinanceAgent(agent_id="test_agent")
        agent._client = MagicMock()
        return agent
    
    @pytest.mark.asyncio
    async def test_process_query_success(self, agent):
        """Test successful query processing"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "success": True,
            "data": {
                "symbol": "AAPL",
                "price": 150.0,
                "timestamp": "2025-11-29T12:00:00",
                "data_source": "finnhub",
                "cache_hit": False
            },
            "cache_hit": False,
            "data_source": "finnhub"
        }
        agent._client.post.return_value = mock_response
        
        result = await agent.process_query("What is the current price of AAPL?")
        
        assert result["success"] == True
        assert result["symbol"] == "AAPL"
        assert result["tool_used"] == "quote.latest"
        assert "insight" in result
    
    @pytest.mark.asyncio
    async def test_process_query_no_symbol(self, agent):
        """Test query without symbol"""
        result = await agent.process_query("What is the price?")
        
        assert result["success"] == False
        assert "symbol" in result["error"].lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
