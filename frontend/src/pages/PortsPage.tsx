import { useEffect, useState } from "react";
import { fetchAllPorts } from "../api/client";
import type { NetworkState } from "../hooks/useNetworkState";
import type { Port } from "../types";
import { deviceName } from "../utils/deviceName";

function formatSpeed(mbps: number): string {
  if (mbps <= 0) return "-";
  return mbps >= 1000 ? `${mbps / 1000} Gbps` : `${mbps} Mbps`;
}

function formatMbps(bps: number): string {
  return (bps / 1_000_000).toFixed(2) + " Mbps";
}

export function PortsPage({ network }: { network: NetworkState }) {
  const [ports, setPorts] = useState<Port[]>([]);
  const deviceById = new Map((network.topology?.devices ?? []).map((d) => [d.id, d]));

  useEffect(() => {
    fetchAllPorts().then(setPorts);
    const interval = setInterval(() => fetchAllPorts().then(setPorts), 10000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="page-scroll">
      <div className="topology-header">
        <strong>Ports</strong>
      </div>
      <div className="list-panel">
        {ports.length === 0 ? (
          <div className="empty-drawer">
            No SNMP port data available across any device yet.
            <br />
            Ports appear here once a device with SNMP enabled responds.
          </div>
        ) : (
          <table className="device-table">
            <thead>
              <tr>
                <th>Device</th>
                <th>Port</th>
                <th>Status</th>
                <th>Speed</th>
                <th>Download</th>
                <th>Upload</th>
              </tr>
            </thead>
            <tbody>
              {ports.map((port) => (
                <tr key={port.id}>
                  <td>
                    {(() => {
                      const dev = deviceById.get(port.device_id);
                      return dev ? deviceName(dev) : port.device_id;
                    })()}
                  </td>
                  <td>{port.name}</td>
                  <td>
                    <span className={`status-pill ${port.status === "up" ? "online" : "offline"}`}>{port.status}</span>
                  </td>
                  <td>{formatSpeed(port.speed_mbps)}</td>
                  <td>{formatMbps(port.rx_bps)}</td>
                  <td>{formatMbps(port.tx_bps)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
