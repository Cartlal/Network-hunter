import dagre from "@dagrejs/dagre";
import {
  Background,
  Controls,
  ReactFlow,
  useEdgesState,
  useNodesState,
  type Edge,
  type Node,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { useCallback, useEffect } from "react";
import type { Device, Topology } from "../types";
import { DeviceNode, type DeviceNodeData } from "./DeviceNode";

const NODE_WIDTH = 140;
const NODE_HEIGHT = 90;
const nodeTypes = { device: DeviceNode };

function edgeLabel(speedMbps: number | null, duplex: string | null, fallback?: string): string | undefined {
  if (!speedMbps) return fallback;
  const speed = speedMbps >= 1000 ? `${speedMbps / 1000} Gbps` : `${speedMbps} Mbps`;
  return duplex ? `${speed} · ${duplex}` : speed;
}

function layout(topology: Topology): { nodes: Node<DeviceNodeData>[]; edges: Edge[] } {
  const graph = new dagre.graphlib.Graph();
  graph.setDefaultEdgeLabel(() => ({}));
  graph.setGraph({ rankdir: "TB", nodesep: 50, ranksep: 90 });

  graph.setNode("internet", { width: NODE_WIDTH, height: NODE_HEIGHT });
  for (const device of topology.devices) {
    graph.setNode(`device-${device.id}`, { width: NODE_WIDTH, height: NODE_HEIGHT });
  }

  const gateway = topology.devices.find((d) => d.is_gateway);
  if (gateway) graph.setEdge("internet", `device-${gateway.id}`);
  for (const link of topology.links) {
    graph.setEdge(`device-${link.from_device_id}`, `device-${link.to_device_id}`);
  }

  dagre.layout(graph);

  const nodes: Node<DeviceNodeData>[] = [
    {
      id: "internet",
      type: "device",
      position: toTopLeft(graph.node("internet")),
      data: { device: {} as Device, isInternet: true },
      draggable: false,
    },
    ...topology.devices.map((device) => {
      const dagrePos = toTopLeft(graph.node(`device-${device.id}`));
      const position = device.pos_x != null && device.pos_y != null ? { x: device.pos_x, y: device.pos_y } : dagrePos;
      return {
        id: `device-${device.id}`,
        type: "device",
        position,
        data: { device } as DeviceNodeData,
      };
    }),
  ];

  const edges: Edge[] = [];
  if (gateway) {
    edges.push({
      id: "internet-gateway",
      source: "internet",
      target: `device-${gateway.id}`,
      animated: gateway.status === "online",
      label: "Uplink",
    });
  }
  for (const link of topology.links) {
    const target = topology.devices.find((d) => d.id === link.to_device_id);
    edges.push({
      id: `link-${link.id}`,
      source: `device-${link.from_device_id}`,
      target: `device-${link.to_device_id}`,
      animated: target?.status === "online",
      label: edgeLabel(link.speed_mbps, link.duplex),
      style: link.inferred ? { strokeDasharray: "4 4" } : undefined,
    });
  }

  return { nodes, edges };
}

function toTopLeft(node: { x: number; y: number } | undefined): { x: number; y: number } {
  if (!node) return { x: 0, y: 0 };
  return { x: node.x - NODE_WIDTH / 2, y: node.y - NODE_HEIGHT / 2 };
}

export function TopologyGraph({
  topology,
  onSelectDevice,
  onNodeDragStop,
}: {
  topology: Topology;
  onSelectDevice: (device: Device) => void;
  onNodeDragStop?: (deviceId: number, x: number, y: number) => void;
}) {
  const [nodes, setNodes, onNodesChange] = useNodesState<Node<DeviceNodeData>>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([]);

  useEffect(() => {
    setNodes((prevNodes) => {
      const { nodes: nextNodes } = layout(topology);
      if (prevNodes.length === 0) return nextNodes;
      // Preserve any in-flight drag position for nodes we already know about;
      // only patch their data (status, bandwidth, etc). New nodes get their
      // freshly computed layout/persisted position.
      const prevIds = new Set(prevNodes.map((n) => n.id));
      const byId = new Map(nextNodes.map((n) => [n.id, n]));
      return prevNodes
        .filter((n) => byId.has(n.id))
        .map((n) => ({ ...n, data: byId.get(n.id)!.data }))
        .concat(nextNodes.filter((n) => !prevIds.has(n.id)));
    });
    setEdges(layout(topology).edges);
  }, [topology, setNodes, setEdges]);

  const handleNodeClick = useCallback(
    (_: unknown, node: Node<DeviceNodeData>) => {
      if (!node.data.isInternet) onSelectDevice(node.data.device);
    },
    [onSelectDevice],
  );

  const handleNodeDragStop = useCallback(
    (_: unknown, node: Node<DeviceNodeData>) => {
      if (!node.data.isInternet && onNodeDragStop) {
        onNodeDragStop(node.data.device.id, node.position.x, node.position.y);
      }
    },
    [onNodeDragStop],
  );

  return (
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
      <Controls />
    </ReactFlow>
  );
}
