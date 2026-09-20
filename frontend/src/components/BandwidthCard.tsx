import type { DeviceBandwidth } from "../hooks/useNetworkState";
import type { Device } from "../types";
import { deviceName } from "../utils/deviceName";

function formatMbps(bps: number): string {
  if (bps >= 1_000_000_000) return `${(bps / 1_000_000_000).toFixed(2)} Gbps`;
  return `${(bps / 1_000_000).toFixed(0)} Mbps`;
}

export function BandwidthCard({
  devices,
  bandwidth,
}: {
  devices: Device[];
  bandwidth: Record<number, DeviceBandwidth>;
}) {
  const rows = devices
    .map((device) => ({ device, total: (bandwidth[device.id]?.rx_bps ?? 0) + (bandwidth[device.id]?.tx_bps ?? 0) }))
    .filter((row) => row.total > 0)
    .sort((a, b) => b.total - a.total)
    .slice(0, 5);

  const maxTotal = rows[0]?.total ?? 1;

  return (
    <div className="stat-card">
      <div className="stat-card-header">
        <strong>Top Devices by Bandwidth</strong>
        <span className="live-badge">
          <span className="live-dot" /> Live
        </span>
      </div>
      {rows.length === 0 ? (
        <div className="empty-drawer">
          No bandwidth data yet.
          <br />
          Enable SNMP on a device to see live throughput.
        </div>
      ) : (
        <div className="bandwidth-rows">
          {rows.map(({ device, total }) => (
            <div className="bandwidth-row" key={device.id}>
              <span className="bandwidth-name">{deviceName(device)}</span>
              <div className="bandwidth-bar-track">
                <div className="bandwidth-bar-fill" style={{ width: `${(total / maxTotal) * 100}%` }} />
              </div>
              <span className="bandwidth-value">{formatMbps(total)}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
