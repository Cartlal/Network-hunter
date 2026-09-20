import { Handle, Position } from "@xyflow/react";
import { Cloud, HelpCircle, Laptop, Monitor, Printer, Router, Smartphone, Cpu } from "lucide-react";
import type { Device } from "../types";
import { deviceName } from "../utils/deviceName";

const ICONS: Record<string, typeof Monitor> = {
  router: Router,
  pc: Monitor,
  laptop: Laptop,
  phone: Smartphone,
  printer: Printer,
  pi: Cpu,
  internet: Cloud,
  unknown: HelpCircle,
};

export interface DeviceNodeData {
  device: Device;
  isInternet?: boolean;
  [key: string]: unknown;
}

export function DeviceNode({ data, selected }: { data: DeviceNodeData; selected: boolean }) {
  const { device, isInternet } = data;
  const Icon = ICONS[isInternet ? "internet" : device.device_type_guess] ?? HelpCircle;
  const name = isInternet ? "Internet" : deviceName(device);

  return (
    <div className={`rf-device-node${selected ? " selected" : ""}`}>
      <Handle type="target" position={Position.Top} style={{ opacity: 0 }} />
      {!isInternet && <span className={`status-dot ${device.status}`} />}
      <Icon size={22} />
      <div className="node-name">{name}</div>
      <div className="node-ip">{isInternet ? "" : device.ip}</div>
      <Handle type="source" position={Position.Bottom} style={{ opacity: 0 }} />
    </div>
  );
}
