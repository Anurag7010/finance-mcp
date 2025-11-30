import React, { useState, useEffect } from "react";
import { Activity, Database, Server } from "lucide-react";
import { mcpApi } from "../services/api";

const StatusBar: React.FC = () => {
  const [status, setStatus] = useState<{
    healthy: boolean;
    redisConnected: boolean;
    subscriptions: number;
  }>({
    healthy: false,
    redisConnected: false,
    subscriptions: 0,
  });

  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const health = await mcpApi.getHealth();
        setStatus({
          healthy: health.status === "healthy",
          redisConnected: health.redis_connected,
          subscriptions: health.active_subscriptions,
        });
        setLoading(false);
      } catch (error) {
        setStatus({
          healthy: false,
          redisConnected: false,
          subscriptions: 0,
        });
        setLoading(false);
      }
    };

    fetchStatus();
    const interval = setInterval(fetchStatus, 5000); // Update every 5 seconds

    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
        <div className="flex items-center gap-2 text-slate-400">
          <div className="w-4 h-4 border-2 border-slate-400 border-t-transparent rounded-full animate-spin" />
          <span className="text-sm">Checking system status...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
      <div className="flex flex-wrap items-center gap-4">
        {/* MCP Server Status */}
        <div className="flex items-center gap-2">
          <Server
            className={`w-4 h-4 ${
              status.healthy ? "text-green-400" : "text-red-400"
            }`}
          />
          <span className="text-sm text-slate-300">
            MCP Server:{" "}
            <span
              className={status.healthy ? "text-green-400" : "text-red-400"}
            >
              {status.healthy ? "Online" : "Offline"}
            </span>
          </span>
        </div>

        {/* Redis Status */}
        <div className="flex items-center gap-2">
          <Database
            className={`w-4 h-4 ${
              status.redisConnected ? "text-green-400" : "text-red-400"
            }`}
          />
          <span className="text-sm text-slate-300">
            Redis:{" "}
            <span
              className={
                status.redisConnected ? "text-green-400" : "text-red-400"
              }
            >
              {status.redisConnected ? "Connected" : "Disconnected"}
            </span>
          </span>
        </div>

        {/* Active Subscriptions */}
        <div className="flex items-center gap-2">
          <Activity className="w-4 h-4 text-blue-400" />
          <span className="text-sm text-slate-300">
            Subscriptions:{" "}
            <span className="text-blue-400">{status.subscriptions}</span>
          </span>
        </div>

        {/* Indicator Dot */}
        <div className="ml-auto flex items-center gap-2">
          <div
            className={`w-2 h-2 rounded-full ${
              status.healthy ? "bg-green-400 animate-pulse" : "bg-red-400"
            }`}
          />
          <span className="text-xs text-slate-400">
            {status.healthy ? "All systems operational" : "System offline"}
          </span>
        </div>
      </div>
    </div>
  );
};

export default StatusBar;
