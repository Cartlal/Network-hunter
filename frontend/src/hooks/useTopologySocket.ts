import { useEffect, useRef } from "react";
import type { SocketMessage } from "../types";

const RECONNECT_DELAY_MS = 2000;

export function useTopologySocket(onMessage: (message: SocketMessage) => void) {
  const callbackRef = useRef(onMessage);
  callbackRef.current = onMessage;

  useEffect(() => {
    let socket: WebSocket | null = null;
    let reconnectTimer: ReturnType<typeof setTimeout> | null = null;
    let closedByEffect = false;

    const connect = () => {
      const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
      socket = new WebSocket(`${protocol}//${window.location.host}/ws/topology`);

      socket.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data) as SocketMessage;
          callbackRef.current(message);
        } catch {
          // ignore malformed frames
        }
      };

      socket.onclose = () => {
        if (!closedByEffect) reconnectTimer = setTimeout(connect, RECONNECT_DELAY_MS);
      };
    };

    connect();

    return () => {
      closedByEffect = true;
      if (reconnectTimer) clearTimeout(reconnectTimer);
      socket?.close();
    };
  }, []);
}
