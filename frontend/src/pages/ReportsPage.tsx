import { Download } from "lucide-react";
import type { NetworkState } from "../hooks/useNetworkState";
import type { Device } from "../types";

function toCsv(devices: Device[]): string {
  const headers = ["IP", "Hostname", "MAC", "Vendor", "Type", "Status", "SNMP Supported", "First Seen", "Last Seen"];
  const rows = devices.map((d) =>
    [d.ip, d.hostname ?? "", d.mac ?? "", d.vendor ?? "", d.device_type_guess, d.status, String(d.snmp_supported ?? ""), d.first_seen, d.last_seen]
      .map((v) => `"${v.replace(/"/g, '""')}"`)
      .join(","),
  );
  return [headers.join(","), ...rows].join("\n");
}

function downloadCsv(devices: Device[]) {
  const csv = toCsv(devices);
  const blob = new Blob([csv], { type: "text/csv" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `netmap-devices-${new Date().toISOString().slice(0, 10)}.csv`;
  a.click();
  URL.revokeObjectURL(url);
}

export function ReportsPage({ network }: { network: NetworkState }) {
  const devices = network.topology?.devices ?? [];
  const online = devices.filter((d) => d.status === "online").length;
  const snmpManaged = devices.filter((d) => d.snmp_supported).length;
  const totalAlerts = network.alerts.length;
  const activeAlerts = network.alerts.filter((a) => !a.resolved_at).length;
  const uptimePct = devices.length ? Math.round((online / devices.length) * 100) : 0;

  return (
    <div className="page-scroll">
      <div className="topology-header">
        <strong>Reports</strong>
      </div>
      <div className="list-panel">
        <div className="report-grid">
          <div className="summary-tile">
            <div className="summary-value">{devices.length}</div>
            <div className="summary-label">Total Devices Discovered</div>
          </div>
          <div className="summary-tile">
            <div className="summary-value">{uptimePct}%</div>
            <div className="summary-label">Currently Online</div>
          </div>
          <div className="summary-tile">
            <div className="summary-value">{snmpManaged}</div>
            <div className="summary-label">SNMP-Managed Devices</div>
          </div>
          <div className="summary-tile">
            <div className="summary-value">
              {activeAlerts} / {totalAlerts}
            </div>
            <div className="summary-label">Active / Total Alerts</div>
          </div>
        </div>
        <button className="export-btn" onClick={() => downloadCsv(devices)}>
          <Download size={16} /> Export Device List (CSV)
        </button>
      </div>
    </div>
  );
}
