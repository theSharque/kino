/**
 * WebSocket hook for real-time updates from backend
 */
import { useState, useEffect, useCallback, useRef } from "react";
import { WS_URL, WS_RECONNECT_DELAY } from "../config/constants";
import { log } from "../lib/logger";

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

type MetricsMessage = { type: "metrics"; data: SystemMetrics };
type FrameUpdatedMessage = { type: "frame_updated"; data: FrameUpdateEvent };
type OtherMessageType = Exclude<string, "metrics" | "frame_updated">;
type OtherMessage = { type: OtherMessageType; data?: unknown };
type WebSocketMessage = MetricsMessage | FrameUpdatedMessage | OtherMessage;

export interface FrameUpdateEvent {
  frame_id: number;
  project_id: number;
  path: string;
  generator: string;
  created_at: string;
  updated_at: string;
}

type FrameUpdateCallback = (event: FrameUpdateEvent | WebSocketMessage) => void;

export const useWebSocket = (onFrameUpdate?: FrameUpdateCallback) => {
  const [metrics, setMetrics] = useState<SystemMetrics | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<number | null>(null);
  const frameUpdateCallbackRef = useRef<FrameUpdateCallback | undefined>(
    onFrameUpdate
  );

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
      log.info("ws_connecting", { url: WS_URL });

      ws.onopen = () => {
        log.info("ws_connected");
        setIsConnected(true);
      };

      ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);

          if (message.type === "metrics") {
            setMetrics((message as MetricsMessage).data);
            log.debug("ws_metrics", (message as MetricsMessage).data);
          } else if (message.type === "frame_updated") {
            log.info("frame_updated", (message as FrameUpdatedMessage).data);
            if (frameUpdateCallbackRef.current) {
              frameUpdateCallbackRef.current(
                (message as FrameUpdatedMessage).data
              );
            }
          } else {
            // Pass all other messages (generation_started, generation_completed, etc.) to callback
            log.info("ws_message", { type: message.type, data: message.data });
            if (frameUpdateCallbackRef.current) {
              frameUpdateCallbackRef.current(message);
            }
          }
        } catch (err) {
          log.error("ws_parse_error", err);
        }
      };

      ws.onerror = (error) => {
        log.error("ws_error", error);
      };

      ws.onclose = () => {
        log.info("ws_disconnected");
        setIsConnected(false);
        wsRef.current = null;

        // Schedule reconnect
        reconnectTimeoutRef.current = window.setTimeout(() => {
          log.info("ws_reconnecting");
          connect();
        }, WS_RECONNECT_DELAY);
      };

      wsRef.current = ws;
    } catch (err) {
      log.error("ws_create_failed", err);
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
      log.debug("ws_send", message);
    }
  }, []);

  // Update callback ref when it changes
  useEffect(() => {
    frameUpdateCallbackRef.current = onFrameUpdate;
  }, [onFrameUpdate]);

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
