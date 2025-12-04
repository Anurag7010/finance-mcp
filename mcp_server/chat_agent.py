"""
Gemini Chat Agent for MCP Server
"""
import asyncio
from typing import Dict, Any, Optional
import google.generativeai as genai

from mcp_server.config import get_settings
from mcp_server.invoke_handlers import handle_quote_latest
from mcp_server.utils.logging import get_logger

logger = get_logger(__name__)

# Exchange rate for INR conversion
USD_TO_INR = 89.94


class GeminiChatAgent:
    """Gemini-powered chat agent with MCP tool access"""
    
    def __init__(self):
        settings = get_settings()
        if not settings.gemini_api_key:
            raise ValueError("GEMINI_API_KEY not configured")
        
        genai.configure(api_key=settings.gemini_api_key)
        self.tools = self._create_tools()
        
    def _create_tools(self):
        """Define Gemini function calling tools"""
        return [
            genai.protos.Tool(
                function_declarations=[
                    genai.protos.FunctionDeclaration(
                        name="get_stock_quote",
                        description="Get the latest stock or cryptocurrency price quote. Use this for any questions about current prices, stock values, market data, or financial instrument values.",
                        parameters=genai.protos.Schema(
                            type=genai.protos.Type.OBJECT,
                            properties={
                                "symbol": genai.protos.Schema(
                                    type=genai.protos.Type.STRING,
                                    description="Stock ticker symbol (e.g., AAPL, MSFT, GOOGL, TSLA) or crypto pair (e.g., BTCUSDT, ETHUSDT, SOLUSDT)"
                                ),
                                "max_age_sec": genai.protos.Schema(
                                    type=genai.protos.Type.INTEGER,
                                    description="Maximum age of cached data in seconds. Default is 60."
                                )
                            },
                            required=["symbol"]
                        )
                    )
                ]
            )
        ]
    
    async def _execute_tool(self, function_name: str, function_args: Dict[str, Any]) -> str:
        """Execute a tool call and return formatted result"""
        
        if function_name == "get_stock_quote":
            symbol = function_args.get("symbol", "AAPL")
            max_age = function_args.get("max_age_sec", 60)
            
            try:
                # Call the MCP handler directly
                result = await handle_quote_latest(
                    symbol=symbol,
                    max_age_sec=max_age,
                    agent_id="gemini_chat_agent",
                    query_text=f"Get quote for {symbol}"
                )
                
                if hasattr(result, 'model_dump'):
                    result = result.model_dump()
                
                if result.get("success") and result.get("data"):
                    data = result["data"]
                    price = data.get("price", 0)
                    price_inr = price * USD_TO_INR
                    
                    response = f"Symbol: {data.get('symbol', symbol)}\\n"
                    response += f"Price: ₹{price_inr:,.2f}\\n"
                    response += f"Source: {data.get('data_source', 'unknown')} ({'cached' if data.get('cache_hit') else 'fresh'})\\n"
                    
                    if data.get("open"):
                        response += f"Open: ₹{(data['open'] * USD_TO_INR):,.2f}\\n"
                    if data.get("high"):
                        response += f"High: ₹{(data['high'] * USD_TO_INR):,.2f}\\n"
                    if data.get("low"):
                        response += f"Low: ₹{(data['low'] * USD_TO_INR):,.2f}\\n"
                    if data.get("previous_close"):
                        prev = data["previous_close"]
                        prev_inr = prev * USD_TO_INR
                        change = price - prev
                        change_inr = change * USD_TO_INR
                        pct = (change / prev) * 100 if prev else 0
                        response += f"Previous Close: ₹{prev_inr:,.2f}\\n"
                        response += f"Change: ₹{change_inr:+,.2f} ({pct:+.2f}%)\\n"
                    if data.get("volume"):
                        response += f"Volume: {data['volume']:,.0f}\\n"
                    
                    return response
                else:
                    return f"Error fetching quote: {result.get('error', 'Unknown error')}"
            
            except Exception as e:
                logger.error(f"Tool execution error: {e}")
                return f"Error executing tool: {str(e)}"
        
        return f"Unknown function: {function_name}"
    
    async def chat(self, message: str, history: Optional[list] = None) -> str:
        """
        Send message to Gemini and return response
        
        Args:
            message: User message
            history: Optional chat history
            
        Returns:
            AI response text
        """
        try:
            # Initialize model
            model = genai.GenerativeModel(
                model_name="gemini-2.5-flash",
                tools=self.tools,
                system_instruction="""You are a helpful financial assistant with access to real-time market data.
                
When users ask about stock prices, crypto values, or market data:
1. Use the get_stock_quote tool to fetch current prices
2. Provide clear, concise analysis of the data
3. All prices are returned in Indian Rupees (₹)
4. Be professional and factual

Common symbol mappings:
- Apple = AAPL, Microsoft = MSFT, Google = GOOGL
- Amazon = AMZN, Tesla = TSLA, NVIDIA = NVDA
- Bitcoin = BTCUSDT, Ethereum = ETHUSDT, Solana = SOLUSDT

Always use tools to get real data - never make up prices."""
            )
            
            # Start or continue chat
            chat = model.start_chat(history=history or [])
            
            # Send user message
            response = chat.send_message(message)
            
            # Handle function calls
            while response.candidates[0].content.parts:
                # Collect all function calls
                function_calls = []
                for part in response.candidates[0].content.parts:
                    if hasattr(part, 'function_call') and part.function_call.name:
                        function_calls.append(part.function_call)
                
                if not function_calls:
                    break
                
                # Execute all functions
                function_responses = []
                for function_call in function_calls:
                    func_name = function_call.name
                    func_args = dict(function_call.args) if function_call.args else {}
                    
                    logger.info(f"Gemini calling: {func_name} with {func_args}")
                    
                    result = await self._execute_tool(func_name, func_args)
                    
                    function_responses.append(
                        genai.protos.Part(
                            function_response=genai.protos.FunctionResponse(
                                name=func_name,
                                response={"result": result}
                            )
                        )
                    )
                
                # Send function results back
                response = chat.send_message(
                    genai.protos.Content(parts=function_responses)
                )
            
            # Extract final text
            final_text = ""
            for part in response.candidates[0].content.parts:
                if hasattr(part, 'text'):
                    final_text += part.text
            
            return final_text
        
        except Exception as e:
            logger.error(f"Chat error: {e}")
            raise


# Singleton instance
_agent_instance: Optional[GeminiChatAgent] = None


def get_chat_agent() -> GeminiChatAgent:
    """Get or create chat agent instance"""
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = GeminiChatAgent()
    return _agent_instance
