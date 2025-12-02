import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
const API_KEY = process.env.REACT_APP_API_KEY || 'dev_key_change_in_production';

// Configure axios to include API key in all requests
axios.defaults.headers.common['X-API-Key'] = API_KEY;

export interface QuoteData {
  symbol: string;
  price: number;
  timestamp: string;
  data_source: string;
  cache_hit: boolean;
  latency_ms: number;
  volume?: number;
  high?: number;
  low?: number;
  open?: number;
  previous_close?: number;
}

export interface QuoteResponse {
  success: boolean;
  data: QuoteData | null;
  error: string | null;
  cache_hit: boolean;
  data_source: string | null;
  latency_ms: number;
}

export interface Capabilities {
  server: {
    name: string;
    version: string;
    description: string;
  };
  tools: Array<{
    name: string;
    description: string;
    inputSchema: any;
    outputSchema: any;
  }>;
  connectors: Array<{
    name: string;
    type: string;
    description: string;
    rate_limit: string;
  }>;
}

export interface HealthStatus {
  status: string;
  redis_connected: boolean;
  active_subscriptions: number;
}

class MCPApi {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  async getHealth(): Promise<HealthStatus> {
    const response = await axios.get<HealthStatus>(`${this.baseUrl}/health`);
    return response.data;
  }

  async getCapabilities(): Promise<Capabilities> {
    const response = await axios.get<Capabilities>(`${this.baseUrl}/capabilities`);
    return response.data;
  }

  async getQuote(symbol: string, maxAgeSec: number = 60): Promise<QuoteResponse> {
    const response = await axios.post<QuoteResponse>(`${this.baseUrl}/invoke`, {
      tool_name: 'quote.latest',
      arguments: {
        symbol: symbol.toUpperCase(),
        maxAgeSec,
      },
      agent_id: 'react_frontend',
      query_text: `Get quote for ${symbol}`,
    });
    return response.data;
  }

  async subscribeStream(symbol: string, channel: 'trades' | 'quotes' = 'trades') {
    const response = await axios.post(`${this.baseUrl}/subscribe`, {
      symbol: symbol.toUpperCase(),
      channel,
      agent_id: 'react_frontend',
    });
    return response.data;
  }

  async unsubscribe(subscriptionId: string) {
    const response = await axios.post(`${this.baseUrl}/unsubscribe`, {
      subscription_id: subscriptionId,
    });
    return response.data;
  }
}

export const mcpApi = new MCPApi();
