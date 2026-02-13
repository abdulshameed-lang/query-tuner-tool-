/**
 * React hook for WebSocket connections with automatic reconnection
 */

import { useEffect, useRef, useState, useCallback } from "react";

export enum WebSocketState {
  CONNECTING = "CONNECTING",
  CONNECTED = "CONNECTED",
  DISCONNECTED = "DISCONNECTED",
  ERROR = "ERROR",
}

export interface WebSocketMessage {
  type: string;
  data?: any;
  timestamp?: number;
  error?: string;
}

export interface UseWebSocketOptions {
  url: string;
  autoConnect?: boolean;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
  heartbeatInterval?: number;
  onOpen?: () => void;
  onClose?: () => void;
  onError?: (error: Event) => void;
  onMessage?: (message: WebSocketMessage) => void;
}

export interface UseWebSocketReturn {
  state: WebSocketState;
  lastMessage: WebSocketMessage | null;
  messages: WebSocketMessage[];
  sendMessage: (message: any) => void;
  connect: () => void;
  disconnect: () => void;
  reconnect: () => void;
  isConnected: boolean;
}

export function useWebSocket(options: UseWebSocketOptions): UseWebSocketReturn {
  const {
    url,
    autoConnect = true,
    reconnectInterval = 3000,
    maxReconnectAttempts = 10,
    heartbeatInterval = 30000,
    onOpen,
    onClose,
    onError,
    onMessage,
  } = options;

  const [state, setState] = useState<WebSocketState>(WebSocketState.DISCONNECTED);
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
  const [messages, setMessages] = useState<WebSocketMessage[]>([]);

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const heartbeatTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const shouldReconnectRef = useRef(true);

  const clearTimeouts = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    if (heartbeatTimeoutRef.current) {
      clearTimeout(heartbeatTimeoutRef.current);
      heartbeatTimeoutRef.current = null;
    }
  }, []);

  const startHeartbeat = useCallback(() => {
    if (heartbeatInterval <= 0) return;

    const sendPing = () => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ type: "ping" }));
      }
    };

    heartbeatTimeoutRef.current = setInterval(sendPing, heartbeatInterval);
  }, [heartbeatInterval]);

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    clearTimeouts();
    setState(WebSocketState.CONNECTING);

    try {
      const ws = new WebSocket(url);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log("WebSocket connected:", url);
        setState(WebSocketState.CONNECTED);
        reconnectAttemptsRef.current = 0;
        startHeartbeat();
        onOpen?.();
      };

      ws.onclose = () => {
        console.log("WebSocket disconnected:", url);
        setState(WebSocketState.DISCONNECTED);
        clearTimeouts();
        onClose?.();

        // Attempt reconnection
        if (
          shouldReconnectRef.current &&
          reconnectAttemptsRef.current < maxReconnectAttempts
        ) {
          reconnectAttemptsRef.current++;
          console.log(
            `Reconnecting... attempt ${reconnectAttemptsRef.current}/${maxReconnectAttempts}`
          );

          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
          }, reconnectInterval * Math.min(reconnectAttemptsRef.current, 5)); // Exponential backoff capped at 5x
        }
      };

      ws.onerror = (error) => {
        console.error("WebSocket error:", error);
        setState(WebSocketState.ERROR);
        onError?.(error);
      };

      ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          setLastMessage(message);
          setMessages((prev) => [...prev.slice(-99), message]); // Keep last 100 messages
          onMessage?.(message);
        } catch (error) {
          console.error("Error parsing WebSocket message:", error);
        }
      };
    } catch (error) {
      console.error("Error creating WebSocket:", error);
      setState(WebSocketState.ERROR);
    }
  }, [
    url,
    reconnectInterval,
    maxReconnectAttempts,
    clearTimeouts,
    startHeartbeat,
    onOpen,
    onClose,
    onError,
    onMessage,
  ]);

  const disconnect = useCallback(() => {
    shouldReconnectRef.current = false;
    clearTimeouts();

    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    setState(WebSocketState.DISCONNECTED);
  }, [clearTimeouts]);

  const reconnect = useCallback(() => {
    disconnect();
    shouldReconnectRef.current = true;
    reconnectAttemptsRef.current = 0;
    connect();
  }, [connect, disconnect]);

  const sendMessage = useCallback((message: any) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      const messageStr = typeof message === "string" ? message : JSON.stringify(message);
      wsRef.current.send(messageStr);
    } else {
      console.warn("WebSocket is not connected. Cannot send message.");
    }
  }, []);

  // Auto-connect on mount
  useEffect(() => {
    if (autoConnect) {
      connect();
    }

    return () => {
      shouldReconnectRef.current = false;
      clearTimeouts();
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [autoConnect, connect, clearTimeouts]);

  return {
    state,
    lastMessage,
    messages,
    sendMessage,
    connect,
    disconnect,
    reconnect,
    isConnected: state === WebSocketState.CONNECTED,
  };
}

/**
 * Hook for monitoring queries in real-time
 */
export function useQueryMonitoring(
  pollInterval: number = 5,
  minElapsedTime: number = 0.1,
  limit: number = 10,
  autoConnect: boolean = true
) {
  const wsUrl = `ws://localhost:8000/api/v1/ws/queries?poll_interval=${pollInterval}&min_elapsed_time=${minElapsedTime}&limit=${limit}`;

  return useWebSocket({
    url: wsUrl,
    autoConnect,
  });
}

/**
 * Hook for monitoring sessions in real-time
 */
export function useSessionMonitoring(
  pollInterval: number = 5,
  showInactive: boolean = false,
  autoConnect: boolean = true
) {
  const wsUrl = `ws://localhost:8000/api/v1/ws/sessions?poll_interval=${pollInterval}&show_inactive=${showInactive}`;

  return useWebSocket({
    url: wsUrl,
    autoConnect,
  });
}

/**
 * Hook for monitoring wait events in real-time
 */
export function useWaitEventsMonitoring(
  pollInterval: number = 5,
  autoConnect: boolean = true
) {
  const wsUrl = `ws://localhost:8000/api/v1/ws/wait-events?poll_interval=${pollInterval}`;

  return useWebSocket({
    url: wsUrl,
    autoConnect,
  });
}

/**
 * Hook for monitoring database metrics in real-time
 */
export function useMetricsMonitoring(
  pollInterval: number = 5,
  autoConnect: boolean = true
) {
  const wsUrl = `ws://localhost:8000/api/v1/ws/metrics?poll_interval=${pollInterval}`;

  return useWebSocket({
    url: wsUrl,
    autoConnect,
  });
}
