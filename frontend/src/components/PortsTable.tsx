import type { Port } from "../types";

function formatSpeed(mbps: number): string {
  if (mbps <= 0) return "-";
  return mbps >= 1000 ? `${mbps / 1000} Gbps` : `${mbps} Mbps`;
}

export function PortsTable({ ports, loading }: { ports: Port[]; loading: boolean }) {
  if (loading) return <div className="empty-drawer">Loading ports...</div>;
  if (ports.length === 0) {
    return (
      <div className="empty-drawer">
        No SNMP port data available.
        <br />
        This device may not support SNMP, or it hasn't responded yet.
      </div>
    );
  }

  return (
    <table className="ports-table">
      <thead>
        <tr>
          <th>Port</th>
          <th>Status</th>
          <th>Speed</th>
          <th>Duplex</th>
        </tr>
      </thead>
      <tbody>
        {ports.map((port) => (
          <tr key={port.id}>
            <td>{port.name}</td>
            <td>
              <span className={`status-pill ${port.status === "up" ? "online" : "offline"}`}>
                {port.status}
              </span>
            </td>
            <td>{formatSpeed(port.speed_mbps)}</td>
            <td>{port.duplex ?? "-"}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
