import { useState } from "react";
import { setDeviceName, setSnmpConfig } from "../api/client";
import type { NetworkState } from "../hooks/useNetworkState";
import { deviceName } from "../utils/deviceName";

export function SettingsPage({ network }: { network: NetworkState }) {
  const devices = network.topology?.devices ?? [];
  const [communityDrafts, setCommunityDrafts] = useState<Record<number, string>>({});
  const [nameDrafts, setNameDrafts] = useState<Record<number, string>>({});
  const [savingId, setSavingId] = useState<number | null>(null);

  const handleToggle = async (deviceId: number, enabled: boolean) => {
    setSavingId(deviceId);
    try {
      await setSnmpConfig(deviceId, { snmp_enabled: enabled, snmp_community: communityDrafts[deviceId] });
    } finally {
      setSavingId(null);
    }
  };

  const handleRename = async (deviceId: number) => {
    const draft = nameDrafts[deviceId];
    if (draft === undefined) return;
    setSavingId(deviceId);
    try {
      await setDeviceName(deviceId, draft.trim() || null);
    } finally {
      setSavingId(null);
    }
  };

  return (
    <div className="page-scroll">
      <div className="topology-header">
        <strong>Settings</strong>
      </div>
      <div className="list-panel">
        <h3 className="settings-section-title">Device Names</h3>
        <p className="settings-hint">
          Not every device announces its own name (some managed switches, appliances, and phones
          don't). Give them a name here - it's used everywhere instead of the raw IP.
        </p>
        <table className="device-table">
          <thead>
            <tr>
              <th>IP Address</th>
              <th>Auto-discovered</th>
              <th>Custom Name</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {devices.map((device) => (
              <tr key={device.id}>
                <td>{device.ip}</td>
                <td>{device.hostname ?? "-"}</td>
                <td>
                  <input
                    className="settings-input"
                    placeholder={deviceName(device)}
                    defaultValue={device.custom_name ?? ""}
                    onChange={(e) => setNameDrafts((prev) => ({ ...prev, [device.id]: e.target.value }))}
                    onBlur={() => handleRename(device.id)}
                  />
                </td>
                <td>{savingId === device.id ? "Saving..." : ""}</td>
              </tr>
            ))}
          </tbody>
        </table>

        <h3 className="settings-section-title">SNMP Device Configuration</h3>
        <p className="settings-hint">
          Most consumer routers, PCs, and phones don't support SNMP. For devices that do (managed
          switches, enterprise APs), set the community string and enable monitoring below.
        </p>
        <table className="device-table">
          <thead>
            <tr>
              <th>Device</th>
              <th>SNMP Supported</th>
              <th>Community String</th>
              <th>Enabled</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {devices.map((device) => (
              <tr key={device.id}>
                <td>{deviceName(device)}</td>
                <td>{device.snmp_supported === null ? "Probing..." : device.snmp_supported ? "Yes" : "No"}</td>
                <td>
                  <input
                    className="settings-input"
                    placeholder="public"
                    defaultValue=""
                    onChange={(e) => setCommunityDrafts((prev) => ({ ...prev, [device.id]: e.target.value }))}
                  />
                </td>
                <td>
                  <input
                    type="checkbox"
                    defaultChecked={device.snmp_enabled}
                    onChange={(e) => handleToggle(device.id, e.target.checked)}
                  />
                </td>
                <td>{savingId === device.id ? "Saving..." : ""}</td>
              </tr>
            ))}
          </tbody>
        </table>

        <h3 className="settings-section-title">About</h3>
        <div className="drawer-field">
          <span className="label">Application</span>
          <span>NetMap Live</span>
        </div>
        <div className="drawer-field">
          <span className="label">Discovery interval</span>
          <span>15s (scan) / 10s (SNMP poll)</span>
        </div>
      </div>
    </div>
  );
}
