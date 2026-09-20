import { useEffect, useState } from "react";
import { fetchDevicePorts } from "../api/client";
import type { DeviceBandwidth } from "../hooks/useNetworkState";
import type { Device, Port } from "../types";
import { deviceName } from "../utils/deviceName";
import { PerformanceChart } from "./PerformanceChart";
import { PortsTable } from "./PortsTable";

type Tab = "overview" | "ports" | "performance";

function formatTime(iso: string): string {
  return new Date(iso).toLocaleString();
}

function formatUptime(seconds: number | null): string {
  if (seconds == null) return "Unknown";
  const days = Math.floor(seconds / 86400);
  const hours = Math.floor((seconds % 86400) / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  return `${days}d ${hours}h ${minutes}m`;
}

export function DeviceDrawer({
  device,
  bandwidth,
  onClose,
}: {
  device: Device | null;
  bandwidth: DeviceBandwidth | undefined;
  onClose: () => void;
}) {
  const [tab, setTab] = useState<Tab>("overview");
  const [ports, setPorts] = useState<Port[]>([]);
  const [loadingPorts, setLoadingPorts] = useState(false);

  useEffect(() => {
    setTab("overview");
    setPorts([]);
  }, [device?.id]);

  useEffect(() => {
    if (tab !== "ports" || !device) return;
    setLoadingPorts(true);
    fetchDevicePorts(device.id)
      .then(setPorts)
      .finally(() => setLoadingPorts(false));
  }, [tab, device]);

  if (!device) {
    return (
      <aside className="device-drawer">
        <div className="empty-drawer">Select a device to see details</div>
      </aside>
    );
  }

  const fields: [string, string][] = [
    ["IP Address", device.ip],
    ["Auto-discovered Name", device.hostname ?? "Unknown"],
    ["MAC Address", device.mac ?? "Unknown"],
    ["Vendor", device.vendor ?? "Unknown"],
    ["Model", device.model ?? "Unknown"],
    ["Type", device.device_type_guess],
    ["Security Score", `${device.security_score} / 100`],
    ["SNMP", device.snmp_supported === null ? "Probing..." : device.snmp_supported ? "Supported" : "Not supported"],
    ["Uptime", device.snmp_supported ? formatUptime(device.uptime_seconds) : "-"],
    ["First Seen", formatTime(device.first_seen)],
    ["Last Seen", formatTime(device.last_seen)],
  ];

  return (
    <aside className="device-drawer">
      <div className="drawer-header">
        <div>
          <div className="drawer-title">{deviceName(device)}</div>
          <span className={`status-pill ${device.status}`}>{device.status === "online" ? "Online" : "Offline"}</span>
        </div>
        <button className="drawer-close" onClick={onClose} aria-label="Close">
          ✕
        </button>
      </div>
      <div className="drawer-tabs">
        {(["overview", "ports", "performance"] as Tab[]).map((t) => (
          <div key={t} className={`drawer-tab${tab === t ? " active" : ""}`} onClick={() => setTab(t)}>
            {t[0].toUpperCase() + t.slice(1)}
          </div>
        ))}
      </div>

      {tab === "overview" &&
        fields.map(([label, value]) => (
          <div className="drawer-field" key={label}>
            <span className="label">{label}</span>
            <span>{value}</span>
          </div>
        ))}

      {tab === "ports" && <PortsTable ports={ports} loading={loadingPorts} />}

      {tab === "performance" && <PerformanceChart deviceId={device.id} liveHistory={bandwidth?.history ?? []} />}
    </aside>
  );
}
