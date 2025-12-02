# Security

## API Key Authentication

The MCP Server uses API key authentication to protect sensitive endpoints.

### Protected Endpoints

- `POST /invoke` - Execute MCP tools
- `POST /subscribe` - Subscribe to real-time streams
- `POST /unsubscribe` - Unsubscribe from streams

### Public Endpoints

- `GET /health` - Health check
- `GET /capabilities` - List available tools
- `GET /.well-known/mcp` - Server metadata
- `GET /subscriptions` - List active subscriptions

### Configuration

Set your API key in the `.env` file:

```bash
MCP_API_KEY=your_secure_key_here
```

**Important:** Change the default key `dev_key_change_in_production` in production environments.

### Usage

#### Frontend (React)

The frontend automatically includes the API key in all requests via axios defaults:

```typescript
// frontend/.env
REACT_APP_API_KEY = your_secure_key_here;
```

#### Python Scripts (Gemini Agent)

Include the API key in request headers:

```python
headers = {"X-API-Key": os.getenv("MCP_API_KEY")}
response = await client.post(f"{MCP_BASE_URL}/invoke", json=payload, headers=headers)
```

#### cURL

```bash
curl -X POST http://localhost:8000/invoke \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your_secure_key_here" \
  -d '{"tool_name": "quote.latest", "arguments": {"symbol": "AAPL"}}'
```

### Error Response

If the API key is missing or invalid, you will receive:

```json
{
  "detail": "Invalid or missing API key"
}
```

HTTP Status: `403 Forbidden`

### Best Practices

1. **Never commit `.env` files** to version control
2. **Use strong, random keys** in production (e.g., UUID or 32+ character strings)
3. **Rotate keys regularly** for production deployments
4. **Use environment-specific keys** (dev, staging, prod)
5. **Consider rate limiting** for additional security (not implemented yet)

### Generating Secure Keys

```bash
# Generate a secure random key (Linux/macOS)
openssl rand -hex 32

# Or use Python
python -c "import secrets; print(secrets.token_urlsafe(32))"
```
