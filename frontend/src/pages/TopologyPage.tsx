import { RefreshCw } from "lucide-react";
import { useState } from "react";
import { triggerTopologyRescan } from "../api/client";
import { DeviceDrawer } from "../components/DeviceDrawer";
import { TopologyGraph } from "../components/TopologyGraph";
import type { NetworkState } from "../hooks/useNetworkState";
import type { Device } from "../types";

export function TopologyPage({ network }: { network: NetworkState }) {
  const { topology, bandwidth, updateDevicePosition, refreshTopology } = network;
  const [selectedDevice, setSelectedDevice] = useState<Device | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  const handleRefresh = async () => {
    setRefreshing(true);
    try {
      await triggerTopologyRescan();
      refreshTopology();
    } finally {
      setRefreshing(false);
    }
  };

  return (
    <>
      <div className="topology-header">
        <div>
          <strong>Network Topology</strong>
          <span className="live-badge">
            <span className="live-dot" /> Live
          </span>
        </div>
        <button className="rescan-btn" disabled={refreshing} onClick={handleRefresh}>
          <RefreshCw size={14} className={refreshing ? "spin" : ""} />
          {refreshing ? "Refreshing..." : "Refresh"}
        </button>
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
