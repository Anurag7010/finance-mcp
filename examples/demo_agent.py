#!/usr/bin/env python3
"""
Minimal Agent Demo Script
Demonstrates end-to-end retrieval through MCP Server

Usage:
    python examples/demo_agent.py
    
Prerequisites:
    1. Start infrastructure: cd infra && docker-compose up -d
    2. Wait for services to be healthy
    3. Run this script
"""
import asyncio
import json
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx


MCP_BASE_URL = "http://localhost:8000"


async def check_health():
    """Check if MCP server is running"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{MCP_BASE_URL}/health")
            data = response.json()
            print(f"✓ MCP Server Status: {data['status']}")
            print(f"  Redis Connected: {data['redis_connected']}")
            print(f"  Active Subscriptions: {data['active_subscriptions']}")
            return True
        except Exception as e:
            print(f"✗ MCP Server not available: {e}")
            return False


async def get_capabilities():
    """Fetch and display MCP capabilities"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{MCP_BASE_URL}/capabilities")
        data = response.json()
        
        print("\n📋 Available MCP Tools:")
        for tool in data.get("tools", []):
            print(f"  • {tool['name']}: {tool['description']}")
        
        print("\n🔌 Available Connectors:")
        for connector in data.get("connectors", []):
            print(f"  • {connector['name']} ({connector['type']}): {connector['rate_limit']}")


async def get_quote(symbol: str, max_age_sec: int = 60):
    """Get latest quote for a symbol"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        payload = {
            "tool_name": "quote.latest",
            "arguments": {
                "symbol": symbol,
                "maxAgeSec": max_age_sec
            },
            "agent_id": "demo_agent",
            "query_text": f"What is the current price of {symbol}?"
        }
        
        print(f"\n📈 Fetching quote for {symbol}...")
        
        response = await client.post(f"{MCP_BASE_URL}/invoke", json=payload)
        result = response.json()
        
        if result.get("success"):
            data = result.get("data", {})
            
            print(f"\n  Symbol: {data.get('symbol')}")
            print(f"  Price: ${data.get('price', 0):,.2f}")
            print(f"  Source: {data.get('data_source')}")
            print(f"  Cache Hit: {data.get('cache_hit')}")
            print(f"  Latency: {data.get('latency_ms', 0):.1f}ms")
            
            if data.get('volume'):
                print(f"  Volume: {data.get('volume'):,.0f}")
            if data.get('high') and data.get('low'):
                print(f"  Range: ${data.get('low'):,.2f} - ${data.get('high'):,.2f}")
            if data.get('previous_close'):
                change = data.get('price', 0) - data.get('previous_close', 0)
                pct = (change / data.get('previous_close', 1)) * 100
                arrow = "📈" if change >= 0 else "📉"
                print(f"  Change: {arrow} ${change:+,.2f} ({pct:+.2f}%)")
        else:
            print(f"  ✗ Error: {result.get('error')}")
        
        return result


async def subscribe_stream(symbol: str, channel: str = "trades"):
    """Subscribe to real-time stream"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        payload = {
            "symbol": symbol,
            "channel": channel,
            "agent_id": "demo_agent"
        }
        
        print(f"\n Subscribing to {symbol} {channel} stream...")
        
        response = await client.post(f"{MCP_BASE_URL}/subscribe", json=payload)
        result = response.json()
        
        if result.get("success"):
            data = result.get("data", {})
            print(f"  ✓ Subscribed!")
            print(f"  Subscription ID: {data.get('subscription_id')}")
            print(f"  Status: {data.get('status')}")
            return data.get('subscription_id')
        else:
            print(f"  ✗ Error: {result.get('error')}")
            return None


async def unsubscribe(subscription_id: str):
    """Unsubscribe from stream"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        payload = {"subscription_id": subscription_id}
        
        print(f"\n⏹ Unsubscribing from {subscription_id}...")
        
        response = await client.post(f"{MCP_BASE_URL}/unsubscribe", json=payload)
        result = response.json()
        
        if result.get("success"):
            print(f"  ✓ Unsubscribed!")
        else:
            print(f"  ✗ Error: {result.get('error')}")


async def list_subscriptions():
    """List active subscriptions"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{MCP_BASE_URL}/subscriptions")
        data = response.json()
        
        subs = data.get("subscriptions", {})
        if subs:
            print(f"\n📡 Active Subscriptions ({len(subs)}):")
            for sub_id, info in subs.items():
                print(f"  • {sub_id}: {info.get('symbol')} ({info.get('channel')})")
        else:
            print("\n📡 No active subscriptions")


async def demo_flow():
    """Run complete demo flow"""
    print("=" * 60)
    print("  Finance MCP Server - Demo Agent")
    print("=" * 60)
    
    # 1. Health check
    if not await check_health():
        print("\n⚠️  Please start the MCP server first:")
        print("   cd infra && docker-compose up -d")
        return
    
    # 2. Show capabilities
    await get_capabilities()
    
    # 3. Get stock quotes
    print("\n" + "-" * 40)
    print("STOCK QUOTES (via Finnhub/Alpha Vantage)")
    print("-" * 40)
    
    await get_quote("AAPL")
    await asyncio.sleep(1)  # Rate limit respect
    
    await get_quote("MSFT")
    await asyncio.sleep(1)
    
    # 4. Get crypto quotes
    print("\n" + "-" * 40)
    print("CRYPTO QUOTES (via Binance)")
    print("-" * 40)
    
    await get_quote("BTCUSDT")
    await asyncio.sleep(0.5)
    
    await get_quote("ETHUSDT")
    
    # 5. Test caching - same symbol should be cached
    print("\n" + "-" * 40)
    print("CACHE TEST (same symbol again)")
    print("-" * 40)
    
    await get_quote("BTCUSDT", max_age_sec=300)  # Should be cached
    
    # 6. Stream subscription demo
    print("\n" + "-" * 40)
    print("STREAMING DEMO")
    print("-" * 40)
    
    sub_id = await subscribe_stream("BTCUSDT", "trades")
    
    if sub_id:
        await list_subscriptions()
        
        print("\n⏳ Waiting 5 seconds for stream data...")
        await asyncio.sleep(5)
        
        # Check if we have new data
        await get_quote("BTCUSDT", max_age_sec=10)
        
        # Unsubscribe
        await unsubscribe(sub_id)
        await list_subscriptions()
    
    # Summary
    print("\n" + "=" * 60)
    print("  Demo Complete!")
    print("=" * 60)
    print("\nKey Observations:")
    print("  1. MCP Server normalizes all connector responses")
    print("  2. Redis cache reduces latency for repeated queries")
    print("  3. Binance WebSocket provides real-time crypto data")
    print("  4. All operations are logged for lineage tracking")
    print("\n🔗 Access Neo4j at http://localhost:7474 to view lineage graph")
    print("   Login: neo4j / password123")


if __name__ == "__main__":
    try:
        asyncio.run(demo_flow())
    except KeyboardInterrupt:
        print("\n\nDemo interrupted.")
