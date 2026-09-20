import { useState } from "react";
import { DeviceDrawer } from "../components/DeviceDrawer";
import { DeviceTable } from "../components/DeviceTable";
import type { NetworkState } from "../hooks/useNetworkState";
import type { Device } from "../types";

export function ClientsPage({ network }: { network: NetworkState }) {
  const { topology, bandwidth } = network;
  const [selectedDevice, setSelectedDevice] = useState<Device | null>(null);
  const clients = (topology?.devices ?? []).filter((d) => !d.is_gateway);

  return (
    <>
      <div className="topology-header">
        <strong>Clients</strong>
        <span className="live-badge" style={{ color: "var(--text-dim)" }}>
          End-user devices (excludes the gateway/router)
        </span>
      </div>
      <div className="topology-body">
        <div className="graph-panel table-panel">
          <DeviceTable devices={clients} onSelectDevice={setSelectedDevice} />
        </div>
        <DeviceDrawer
          device={selectedDevice}
          bandwidth={selectedDevice ? bandwidth[selectedDevice.id] : undefined}
          onClose={() => setSelectedDevice(null)}
        />
      </div>
    </>
  );
}
