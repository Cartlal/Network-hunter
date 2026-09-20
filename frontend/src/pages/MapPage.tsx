import { Background, ReactFlow, useEdgesState, useNodesState, type Node } from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { useCallback, useEffect, useState } from "react";
import { setDeviceMapPosition } from "../api/client";
import { DeviceDrawer } from "../components/DeviceDrawer";
import { DeviceNode, type DeviceNodeData } from "../components/DeviceNode";
import type { NetworkState } from "../hooks/useNetworkState";
import type { Device } from "../types";

const nodeTypes = { device: DeviceNode };
const GRID_COLS = 6;
const GRID_SPACING = 160;

function buildMapNodes(devices: Device[]): Node<DeviceNodeData>[] {
  return devices.map((device, i) => ({
    id: `device-${device.id}`,
    type: "device",
    position:
      device.map_x != null && device.map_y != null
        ? { x: device.map_x, y: device.map_y }
        : { x: (i % GRID_COLS) * GRID_SPACING, y: Math.floor(i / GRID_COLS) * GRID_SPACING },
    data: { device },
  }));
}

export function MapPage({ network }: { network: NetworkState }) {
  const devices = network.topology?.devices ?? [];
  const [nodes, setNodes, onNodesChange] = useNodesState<Node<DeviceNodeData>>([]);
  const [edges, , onEdgesChange] = useEdgesState([]);
  const [selectedDevice, setSelectedDevice] = useState<Device | null>(null);

  useEffect(() => {
    setNodes((prev) => {
      const next = buildMapNodes(devices);
      if (prev.length === 0) return next;
      const byId = new Map(next.map((n) => [n.id, n]));
      const prevIds = new Set(prev.map((n) => n.id));
      return prev
        .filter((n) => byId.has(n.id))
        .map((n) => ({ ...n, data: byId.get(n.id)!.data }))
        .concat(next.filter((n) => !prevIds.has(n.id)));
    });
  }, [devices, setNodes]);

  const handleNodeClick = useCallback((_: unknown, node: Node<DeviceNodeData>) => {
    setSelectedDevice(node.data.device);
  }, []);

  const handleNodeDragStop = useCallback((_: unknown, node: Node<DeviceNodeData>) => {
    setDeviceMapPosition(node.data.device.id, node.position.x, node.position.y).catch(() => {});
  }, []);

  return (
    <>
      <div className="topology-header">
        <strong>Map</strong>
        <span className="live-badge" style={{ color: "var(--text-dim)" }}>
          Drag devices to arrange their physical layout
        </span>
      </div>
      <div className="topology-body">
        <div className="graph-panel">
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onNodeClick={handleNodeClick}
            onNodeDragStop={handleNodeDragStop}
            nodeTypes={nodeTypes}
            fitView
            colorMode="dark"
          >
            <Background />
          </ReactFlow>
        </div>
        <DeviceDrawer
          device={selectedDevice}
          bandwidth={selectedDevice ? network.bandwidth[selectedDevice.id] : undefined}
          onClose={() => setSelectedDevice(null)}
        />
      </div>
    </>
  );
}
