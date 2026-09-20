import { useState } from "react";
import { DeviceDrawer } from "../components/DeviceDrawer";
import { DeviceTable } from "../components/DeviceTable";
import type { NetworkState } from "../hooks/useNetworkState";
import type { Device } from "../types";

export function DevicesPage({ network }: { network: NetworkState }) {
  const { topology, bandwidth } = network;
  const [selectedDevice, setSelectedDevice] = useState<Device | null>(null);

  return (
    <>
      <div className="topology-header">
        <strong>Devices</strong>
      </div>
      <div className="topology-body">
        <div className="graph-panel table-panel">
          <DeviceTable devices={topology?.devices ?? []} onSelectDevice={setSelectedDevice} />
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
