#!/usr/bin/env python3
"""
Gemini + Finance MCP Server Integration

"""
import os
import httpx
import asyncio
import google.generativeai as genai
from typing import Dict, Any, Optional
from dotenv import load_dotenv


# Load environment variables
load_dotenv()

# ============ CONFIGURATION ============
MCP_BASE_URL = os.getenv("MCP_BASE_URL", "http://localhost:8000")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

if not GEMINI_API_KEY:
    print("Error: GEMINI_API_KEY not set in .env")
    
    exit(1)

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)


# ============ MCP TOOL FUNCTIONS ============
async def call_mcp_quote(symbol: str, max_age_sec: int = 60) -> Dict[str, Any]:
    """Fetch quote from MCP"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        payload = {
            "tool_name": "quote.latest",
            "arguments": {"symbol": symbol.upper(), "maxAgeSec": max_age_sec},
            "agent_id": "gemini_agent",
            "query_text": f"Get quote for {symbol}"
        }
        try:
            response = await client.post(f"{MCP_BASE_URL}/invoke", json=payload)
            return response.json()
        except Exception as e:
            return {"success": False, "error": str(e)}


async def call_mcp_subscribe(symbol: str, channel: str = "trades") -> Dict[str, Any]:
    """Subscribe to real-time stream"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        payload = {
            "symbol": symbol.upper(),
            "channel": channel,
            "agent_id": "gemini_agent"
        }
        try:
            response = await client.post(f"{MCP_BASE_URL}/subscribe", json=payload)
            return response.json()
        except Exception as e:
            return {"success": False, "error": str(e)}


# ============ TOOL EXECUTION ============
def execute_tool(function_name: str, function_args: Dict[str, Any]) -> str:
    """Execute a tool call and return formatted result"""
    
    if function_name == "get_stock_quote":
        symbol = function_args.get("symbol", "AAPL")
        max_age = function_args.get("max_age_sec", 60)
        
        # Run async function
        result = asyncio.run(call_mcp_quote(symbol, max_age))
        
        if result.get("success"):
            data = result["data"]
            price = data.get("price", 0)
            source = data.get("data_source", "unknown")
            cache_hit = "cached" if data.get("cache_hit") else "fresh"
            
            response = f"Symbol: {data.get('symbol', symbol)}\n"
            response += f"Price: ${price:,.2f}\n"
            response += f"Source: {source} ({cache_hit})\n"
            
            if data.get("open"):
                response += f"Open: ${data['open']:,.2f}\n"
            if data.get("high"):
                response += f"High: ${data['high']:,.2f}\n"
            if data.get("low"):
                response += f"Low: ${data['low']:,.2f}\n"
            if data.get("previous_close"):
                prev = data["previous_close"]
                change = price - prev
                pct = (change / prev) * 100 if prev else 0
                response += f"Previous Close: ${prev:,.2f}\n"
                response += f"Change: ${change:+,.2f} ({pct:+.2f}%)\n"
            if data.get("volume"):
                response += f"Volume: {data['volume']:,.0f}\n"
            
            return response
        else:
            return f"Error fetching quote: {result.get('error', 'Unknown error')}"
    
    elif function_name == "subscribe_realtime":
        symbol = function_args.get("symbol", "BTCUSDT")
        channel = function_args.get("channel", "trades")
        
        result = asyncio.run(call_mcp_subscribe(symbol, channel))
        
        if result.get("subscription_id"):
            return f"✓ Subscribed to {symbol} {channel} stream\nSubscription ID: {result['subscription_id']}"
        else:
            return f"Error subscribing: {result.get('error', 'Unknown error')}"
    
    else:
        return f"Unknown function: {function_name}"


# ============ GEMINI TOOL DEFINITIONS ============
tools = [
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
            ),
            genai.protos.FunctionDeclaration(
                name="subscribe_realtime",
                description="Subscribe to real-time price updates for a cryptocurrency. Use when user wants live streaming data.",
                parameters=genai.protos.Schema(
                    type=genai.protos.Type.OBJECT,
                    properties={
                        "symbol": genai.protos.Schema(
                            type=genai.protos.Type.STRING,
                            description="Crypto pair symbol (e.g., BTCUSDT, ETHUSDT)"
                        ),
                        "channel": genai.protos.Schema(
                            type=genai.protos.Type.STRING,
                            description="Stream channel type: 'trades' or 'quotes'"
                        )
                    },
                    required=["symbol"]
                )
            )
        ]
    )
]


# ============ CHAT WITH GEMINI ============
def chat_with_gemini(user_message: str, chat_history: Optional[list] = None) -> str:
    """
    Send message to Gemini with MCP tool access
    and return the response text.
    """
    # Initialize model with tools
    model = genai.GenerativeModel(
        model_name="gemini-2.0-flash",  # Free tier, latest model
        tools=tools,
        system_instruction="""You are a helpful financial assistant with access to real-time market data.
        
When users ask about stock prices, crypto values, or market data:
1. Use the get_stock_quote tool to fetch current prices
2. Provide clear, concise analysis of the data
3. Include relevant metrics like price change, volume when available

Common symbol mappings:
- Apple = AAPL
- Microsoft = MSFT  
- Google/Alphabet = GOOGL
- Amazon = AMZN
- Tesla = TSLA
- NVIDIA = NVDA
- Bitcoin = BTCUSDT
- Ethereum = ETHUSDT
- Solana = SOLUSDT

Always use the tools to get real data - never make up prices."""
    )
    
    # Start or continue chat
    chat = model.start_chat(history=chat_history or [])
    
    # Send user message
    response = chat.send_message(user_message)
    
    # Handle function calls 
    while response.candidates[0].content.parts:
        # Collect ALL function calls from the response
        function_calls = []
        for part in response.candidates[0].content.parts:
            if hasattr(part, 'function_call') and part.function_call.name:
                function_calls.append(part.function_call)
        
        if not function_calls:
            break
        
        # Execute all functions and collect responses
        function_responses = []
        for function_call in function_calls:
            func_name = function_call.name
            func_args = dict(function_call.args) if function_call.args else {}
            
            print(f"\n🔧 Gemini calling: {func_name}")
            print(f"   Arguments: {func_args}")
            
            # Execute the function
            result = execute_tool(func_name, func_args)
            print(f" Result:\n{result}\n")
            
            function_responses.append(
                genai.protos.Part(
                    function_response=genai.protos.FunctionResponse(
                        name=func_name,
                        response={"result": result}
                    )
                )
            )
        
        # Send ALL function results back to Gemini at once
        response = chat.send_message(
            genai.protos.Content(parts=function_responses)
        )
    
    # Extract final text response
    final_text = ""
    for part in response.candidates[0].content.parts:
        if hasattr(part, 'text'):
            final_text += part.text
    
    return final_text


# ============ INTERACTIVE CLI ============
def interactive_mode():
    """Interactive chat"""
    print("=" * 60)
    print("  Gemini + Finance MCP Agent")
    
    print("\nExamples:")
    print("  • What's the price of Apple stock?")
    print("  • How much is Bitcoin worth?")
    print("  • Compare Tesla and NVIDIA prices")
    print("\n'exit' to stop.\n")
    print("-" * 60)
    
    chat_history = []
    
    while True:
        try:
            user_input = input("\nYou: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("\nGoodbye!")
                break
            
            print("\nGemini: ", end="")
            
            response = chat_with_gemini(user_input, chat_history)
            print(response)
            
            # Update history for context
            chat_history.append({"role": "user", "parts": [user_input]})
            chat_history.append({"role": "model", "parts": [response]})
            
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"\nError: {e}")


# ============ DEMO MODE ============
def demo_mode():
    
    print("=" * 60)
    print("  Gemini + Finance MCP Demo")
    print("=" * 60)
    
    demo_queries = [
        "What's the current price of Apple stock?",
        "How much is Bitcoin trading at right now?",
        "Can you compare Microsoft and Google stock prices?",
        "What's Ethereum worth today?"
    ]
    
    for query in demo_queries:
        print(f"\n{'='*60}")
        print(f"User: {query}")
        print("-" * 60)
        
        try:
            response = chat_with_gemini(query)
            print(f"\n  Gemini: {response}")
        except Exception as e:
            print(f"\nError: {e}")
        
        print()


# ============ MAIN ============
if __name__ == "__main__":
    import sys
    
    # Check MCP server health first
    async def check_mcp():
        async with httpx.AsyncClient(timeout=5.0) as client:
            try:
                response = await client.get(f"{MCP_BASE_URL}/health")
                return response.json().get("status") == "healthy"
            except:
                return False
    
    print("Checking MCP server...")
    if not asyncio.run(check_mcp()):
        print("MCP server not running")
        print("   Start with: cd infra && docker-compose up -d")
        exit(1)
    print("MCP server is healthy\n")
    
    # Run mode based on argument
    if len(sys.argv) > 1 and sys.argv[1] == "--demo":
        demo_mode()
    else:
        interactive_mode()
