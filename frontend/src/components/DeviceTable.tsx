import type { Device } from "../types";
import { deviceName } from "../utils/deviceName";
import { formatRelativeTime } from "../utils/time";

export function DeviceTable({ devices, onSelectDevice }: { devices: Device[]; onSelectDevice: (d: Device) => void }) {
  if (devices.length === 0) {
    return <div className="empty-drawer">No devices found.</div>;
  }

  return (
    <table className="device-table">
      <thead>
        <tr>
          <th></th>
          <th>Name</th>
          <th>IP Address</th>
          <th>MAC Address</th>
          <th>Vendor</th>
          <th>Type</th>
          <th>SNMP</th>
          <th>Last Seen</th>
        </tr>
      </thead>
      <tbody>
        {devices.map((device) => (
          <tr key={device.id} onClick={() => onSelectDevice(device)}>
            <td>
              <span className={`status-dot-inline ${device.status}`} />
            </td>
            <td>{deviceName(device)}</td>
            <td>{device.ip}</td>
            <td>{device.mac ?? "-"}</td>
            <td>{device.vendor ?? "Unknown"}</td>
            <td>{device.device_type_guess}</td>
            <td>{device.snmp_supported === null ? "-" : device.snmp_supported ? "Yes" : "No"}</td>
            <td>{formatRelativeTime(device.last_seen)}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
