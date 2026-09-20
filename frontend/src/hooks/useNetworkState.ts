import { useCallback, useEffect, useState } from "react";
import {
  fetchActivity,
  fetchAlerts,
  fetchSecurityFindings,
  fetchSecurityOverview,
  fetchTopology,
  setDevicePosition,
} from "../api/client";
import { useTopologySocket } from "./useTopologySocket";
import type { Activity, Alert, Device, SecurityFinding, SecurityOverview, SocketMessage, Topology } from "../types";

export interface BandwidthSample {
  t: number;
  rx_bps: number;
  tx_bps: number;
}

export interface DeviceBandwidth {
  rx_bps: number;
  tx_bps: number;
  history: BandwidthSample[];
}

const HISTORY_LENGTH = 60;

export function useNetworkState() {
  const [topology, setTopology] = useState<Topology | null>(null);
  const [bandwidth, setBandwidth] = useState<Record<number, DeviceBandwidth>>({});
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [activity, setActivity] = useState<Activity[]>([]);
  const [securityOverview, setSecurityOverview] = useState<SecurityOverview | null>(null);
  const [securityFindings, setSecurityFindings] = useState<SecurityFinding[]>([]);

  const refreshAlerts = useCallback(() => {
    fetchAlerts().then(setAlerts);
  }, []);
  const refreshActivity = useCallback(() => {
    fetchActivity().then(setActivity);
  }, []);
  const refreshSecurity = useCallback(() => {
    fetchSecurityOverview().then(setSecurityOverview);
    fetchSecurityFindings().then(setSecurityFindings);
  }, []);

  useEffect(() => {
    fetchTopology().then(setTopology);
    refreshAlerts();
    refreshActivity();
    refreshSecurity();
  }, [refreshAlerts, refreshActivity, refreshSecurity]);

  const handleMessage = useCallback(
    (message: SocketMessage) => {
      if (message.type === "device_status") {
        setTopology((prev) => {
          if (!prev) return prev;
          const byId = new Map(message.devices.map((d) => [d.id, d]));
          return {
            ...prev,
            devices: prev.devices.map((d) =>
              byId.has(d.id) ? ({ ...d, ...byId.get(d.id) } as Device) : d,
            ),
          };
        });
        refreshActivity();
      } else if (message.type === "port_metrics") {
        setBandwidth((prev) => {
          const next = { ...prev };
          const totals = new Map<number, { rx: number; tx: number }>();
          for (const port of message.ports) {
            const running = totals.get(port.device_id) ?? { rx: 0, tx: 0 };
            running.rx += port.rx_bps;
            running.tx += port.tx_bps;
            totals.set(port.device_id, running);
          }
          const now = Date.now();
          for (const [deviceId, { rx, tx }] of totals) {
            const existing = next[deviceId]?.history ?? [];
            next[deviceId] = {
              rx_bps: rx,
              tx_bps: tx,
              history: [...existing, { t: now, rx_bps: rx, tx_bps: tx }].slice(-HISTORY_LENGTH),
            };
          }
          return next;
        });
      } else if (message.type === "topology_changed") {
        fetchTopology().then(setTopology);
      } else if (message.type === "alerts_changed") {
        refreshAlerts();
        refreshActivity();
      } else if (message.type === "security_findings_changed") {
        refreshSecurity();
      }
    },
    [refreshAlerts, refreshActivity, refreshSecurity],
  );

  useTopologySocket(handleMessage);

  const updateDevicePosition = useCallback((deviceId: number, x: number, y: number) => {
    setTopology((prev) =>
      prev
        ? { ...prev, devices: prev.devices.map((d) => (d.id === deviceId ? { ...d, pos_x: x, pos_y: y } : d)) }
        : prev,
    );
    setDevicePosition(deviceId, x, y).catch(() => {
      // best-effort persistence - the drag already reflects locally
    });
  }, []);

  return {
    topology,
    bandwidth,
    alerts,
    activity,
    securityOverview,
    securityFindings,
    refreshSecurity,
    updateDevicePosition,
  };
}

export type NetworkState = ReturnType<typeof useNetworkState>;
