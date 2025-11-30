"""
Finance MCP Server
Main FastAPI application
"""
import json
from pathlib import Path
from contextlib import asynccontextmanager
from typing import Optional
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from mcp_server.config import get_settings
from mcp_server.utils.logging import setup_logging, get_logger
from mcp_server.schemas import ToolInvocation, ToolResponse, SubscriptionRequest
from mcp_server.invoke_handlers import (
    handle_quote_latest,
    handle_quote_stream,
    handle_unsubscribe,
    get_active_subscriptions
)
from cache.redis_client import get_redis_client
from cache.qdrant_client import get_semantic_cache
from graph.lineage_writer import get_lineage_writer

# Setup logging
setup_logging()
logger = get_logger(__name__)

# Load capabilities
CAPABILITIES_PATH = Path(__file__).parent / "capabilities.json"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler"""
    logger.info("mcp_server_starting")
    
    # Initialize Redis
    redis_client = get_redis_client()
    if redis_client.connect():
        logger.info("redis_initialized")
    else:
        logger.warning("redis_connection_failed")
    
    # Initialize Qdrant
    semantic_cache = get_semantic_cache()
    if semantic_cache.initialize():
        logger.info("qdrant_initialized")
    else:
        logger.warning("qdrant_initialization_failed")
    
    # Initialize Neo4j lineage
    lineage_writer = get_lineage_writer()
    if lineage_writer.initialize():
        logger.info("neo4j_initialized")
    else:
        logger.warning("neo4j_initialization_failed")
    
    logger.info("mcp_server_started")
    
    yield
    
    # Cleanup
    logger.info("mcp_server_stopping")
    redis_client.close()


# Create FastAPI app
settings = get_settings()
app = FastAPI(
    title=settings.mcp_server_name,
    version=settings.mcp_server_version,
    description="Real-Time Financial Data MCP Integration System",
    lifespan=lifespan
)

# Add CORS middleware to allow frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=False,  # Must be False when allow_origins is "*"
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
)


# ==================== CORS PREFLIGHT HANDLER ====================
# Explicit handler for CORS preflight requests
from fastapi import Response

@app.options("/{path:path}")
async def options_handler(path: str):
    """Handle CORS preflight requests for all paths"""
    return Response(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, PATCH",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Max-Age": "86400",
        }
    )


# ==================== MCP ENDPOINTS ====================

@app.get("/.well-known/mcp")
async def mcp_metadata():
    """
    MCP metadata endpoint
    Returns server information and protocol version
    """
    return {
        "name": settings.mcp_server_name,
        "version": settings.mcp_server_version,
        "protocol_version": "1.0",
        "description": "Real-Time Financial Data MCP Integration System",
        "capabilities": ["tools", "subscriptions"],
        "endpoints": {
            "capabilities": "/capabilities",
            "invoke": "/invoke",
            "subscribe": "/subscribe",
            "unsubscribe": "/unsubscribe"
        }
    }


@app.get("/capabilities")
async def get_capabilities():
    """
    Returns available MCP tools and connectors
    """
    try:
        with open(CAPABILITIES_PATH, "r") as f:
            capabilities = json.load(f)
        return capabilities
    except FileNotFoundError:
        logger.error("capabilities_file_not_found")
        raise HTTPException(status_code=500, detail="Capabilities file not found")
    except json.JSONDecodeError:
        logger.error("capabilities_json_error")
        raise HTTPException(status_code=500, detail="Invalid capabilities file")


@app.post("/invoke")
async def invoke_tool(request: ToolInvocation):
    """
    Execute an MCP tool
    
    Supported tools:
    - quote.latest: Get latest price quote
    - quote.stream: Subscribe to real-time stream
    """
    logger.info(
        "invoke_request",
        tool=request.tool_name,
        args=request.arguments
    )
    
    try:
        tool_name = request.tool_name.lower()
        args = request.arguments
        
        if tool_name == "quote.latest":
            response = await handle_quote_latest(
                symbol=args.get("symbol"),
                exchange=args.get("exchange"),
                max_age_sec=args.get("maxAgeSec"),
                agent_id=request.agent_id,
                query_text=request.query_text
            )
        
        elif tool_name == "quote.stream":
            response = await handle_quote_stream(
                symbol=args.get("symbol"),
                channel=args.get("channel", "trades"),
                agent_id=request.agent_id
            )
        
        else:
            response = ToolResponse(
                success=False,
                error=f"Unknown tool: {tool_name}. Available tools: quote.latest, quote.stream"
            )
        
        if response.success:
            return JSONResponse(content=response.model_dump())
        else:
            return JSONResponse(
                status_code=400,
                content=response.model_dump()
            )
            
    except Exception as e:
        logger.error("invoke_error", error=str(e))
        return JSONResponse(
            status_code=500,
            content=ToolResponse(
                success=False,
                error=f"Internal error: {str(e)}"
            ).model_dump()
        )


@app.post("/subscribe")
async def subscribe(request: SubscriptionRequest):
    """
    Subscribe to a real-time stream
    """
    logger.info(
        "subscribe_request",
        symbol=request.symbol,
        channel=request.channel
    )
    
    try:
        response = await handle_quote_stream(
            symbol=request.symbol,
            channel=request.channel,
            agent_id=request.agent_id
        )
        
        if response.success:
            return JSONResponse(content=response.model_dump())
        else:
            return JSONResponse(
                status_code=400,
                content=response.model_dump()
            )
            
    except Exception as e:
        logger.error("subscribe_error", error=str(e))
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )


class UnsubscribeRequest(BaseModel):
    subscription_id: str


@app.post("/unsubscribe")
async def unsubscribe(request: UnsubscribeRequest):
    """
    Unsubscribe from a stream
    """
    logger.info("unsubscribe_request", subscription_id=request.subscription_id)
    
    try:
        response = await handle_unsubscribe(request.subscription_id)
        
        if response.success:
            return JSONResponse(content=response.model_dump())
        else:
            return JSONResponse(
                status_code=400,
                content=response.model_dump()
            )
            
    except Exception as e:
        logger.error("unsubscribe_error", error=str(e))
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )


# ==================== UTILITY ENDPOINTS ====================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    redis_client = get_redis_client()
    
    return {
        "status": "healthy",
        "redis_connected": redis_client.is_connected(),
        "active_subscriptions": len(get_active_subscriptions())
    }


@app.get("/subscriptions")
async def list_subscriptions():
    """List active subscriptions"""
    return {
        "subscriptions": get_active_subscriptions()
    }


# ==================== ERROR HANDLERS ====================

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("unhandled_exception", error=str(exc), path=request.url.path)
    return JSONResponse(
        status_code=500,
        content={"success": False, "error": "Internal server error"}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "mcp_server.server:app",
        host=settings.mcp_server_host,
        port=settings.mcp_server_port,
        reload=True
    )
