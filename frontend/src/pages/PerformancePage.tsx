import { useState } from "react";
import { PerformanceChart } from "../components/PerformanceChart";
import type { NetworkState } from "../hooks/useNetworkState";
import { deviceName } from "../utils/deviceName";

export function PerformancePage({ network }: { network: NetworkState }) {
  const devices = network.topology?.devices ?? [];
  const [selectedId, setSelectedId] = useState<number | null>(devices[0]?.id ?? null);
  const selected = devices.find((d) => d.id === selectedId) ?? devices[0];

  return (
    <div className="page-scroll">
      <div className="topology-header">
        <strong>Performance</strong>
      </div>
      <div className="list-panel">
        <div className="device-picker">
          <label>Device:</label>
          <select value={selected?.id ?? ""} onChange={(e) => setSelectedId(Number(e.target.value))}>
            {devices.map((d) => (
              <option key={d.id} value={d.id}>
                {deviceName(d)} {d.snmp_supported ? "" : "(no SNMP)"}
              </option>
            ))}
          </select>
        </div>
        {selected ? (
          <PerformanceChart deviceId={selected.id} liveHistory={network.bandwidth[selected.id]?.history ?? []} />
        ) : (
          <div className="empty-drawer">No devices discovered yet.</div>
        )}
      </div>
    </div>
  );
}
