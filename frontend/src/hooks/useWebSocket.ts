/**
 * WebSocket hook for real-time updates from backend
 */
import { useState, useEffect, useCallback, useRef } from "react";
import { WS_URL, WS_RECONNECT_DELAY } from "../config/constants";

export interface SystemMetrics {
  cpu_percent: number;
  memory_percent: number;
  gpu_percent: number;
  gpu_memory_percent: number;
  gpu_available: boolean;
  gpu_type: string; // 'xpu' (Intel Arc), 'cuda' (NVIDIA), or 'none'
  pending_count: number;
  running_count: number;
  current_task: {
    id: number;
    name: string;
    progress: number;
  } | null;
}

interface WebSocketMessage {
  type: string;
  data?: any;
}

export const useWebSocket = () => {
  const [metrics, setMetrics] = useState<SystemMetrics | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<number | null>(null);

  const connect = useCallback(() => {
    // Clear any pending reconnect
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    // Close existing connection
    if (wsRef.current) {
      wsRef.current.close();
    }

    try {
      const ws = new WebSocket(WS_URL);

      ws.onopen = () => {
        console.log("📡 WebSocket connected");
        setIsConnected(true);
      };

      ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);

          if (message.type === "metrics" && message.data) {
            setMetrics(message.data);
          }
        } catch (err) {
          console.error("Failed to parse WebSocket message:", err);
        }
      };

      ws.onerror = (error) => {
        console.error("WebSocket error:", error);
      };

      ws.onclose = () => {
        console.log("📡 WebSocket disconnected");
        setIsConnected(false);
        wsRef.current = null;

        // Schedule reconnect
        reconnectTimeoutRef.current = window.setTimeout(() => {
          console.log("🔄 Reconnecting WebSocket...");
          connect();
        }, WS_RECONNECT_DELAY);
      };

      wsRef.current = ws;
    } catch (err) {
      console.error("Failed to create WebSocket:", err);
      setIsConnected(false);

      // Schedule reconnect
      reconnectTimeoutRef.current = window.setTimeout(() => {
        connect();
      }, WS_RECONNECT_DELAY);
    }
  }, []);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    setIsConnected(false);
  }, []);

  const sendMessage = useCallback((message: WebSocketMessage) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
    }
  }, []);

  // Connect on mount, disconnect on unmount
  useEffect(() => {
    connect();

    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

  return {
    metrics,
    isConnected,
    sendMessage,
    reconnect: connect,
  };
};
