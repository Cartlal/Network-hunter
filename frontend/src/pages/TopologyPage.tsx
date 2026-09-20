import { useState } from "react";
import { DeviceDrawer } from "../components/DeviceDrawer";
import { TopologyGraph } from "../components/TopologyGraph";
import type { NetworkState } from "../hooks/useNetworkState";
import type { Device } from "../types";

export function TopologyPage({ network }: { network: NetworkState }) {
  const { topology, bandwidth, updateDevicePosition } = network;
  const [selectedDevice, setSelectedDevice] = useState<Device | null>(null);

  return (
    <>
      <div className="topology-header">
        <div>
          <strong>Network Topology</strong>
          <span className="live-badge">
            <span className="live-dot" /> Live
          </span>
        </div>
      </div>
      <div className="topology-body">
        <div className="graph-panel">
          {topology && (
            <TopologyGraph
              topology={topology}
              onSelectDevice={setSelectedDevice}
              onNodeDragStop={updateDevicePosition}
            />
          )}
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
