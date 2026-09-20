export type DeviceStatus = "online" | "offline";

export type Page =
  | "security"
  | "dashboard"
  | "topology"
  | "devices"
  | "clients"
  | "map"
  | "alerts"
  | "performance"
  | "ports"
  | "reports"
  | "logs"
  | "settings";

export interface Device {
  id: number;
  ip: string;
  mac: string | null;
  hostname: string | null;
  custom_name: string | null;
  vendor: string | null;
  device_type_guess: string;
  is_gateway: boolean;
  status: DeviceStatus;
  first_seen: string;
  last_seen: string;
  model: string | null;
  firmware: string | null;
  uptime_seconds: number | null;
  snmp_enabled: boolean;
  snmp_supported: boolean | null;
  pos_x: number | null;
  pos_y: number | null;
  map_x: number | null;
  map_y: number | null;
  security_score: number;
}

export interface Link {
  id: number;
  from_device_id: number;
  to_device_id: number;
  inferred: boolean;
  speed_mbps: number | null;
  duplex: string | null;
}

export interface Topology {
  devices: Device[];
  links: Link[];
}

export interface Port {
  id: number;
  device_id: number;
  if_index: number;
  name: string;
  status: "up" | "down" | "unknown";
  speed_mbps: number;
  duplex: string | null;
  rx_bps: number;
  tx_bps: number;
}

export interface DeviceStatusUpdate {
  id: number;
  ip: string;
  status: DeviceStatus;
  last_seen: string;
}

export interface PortMetricUpdate {
  device_id: number;
  if_index: number;
  status: string;
  speed_mbps: number;
  rx_bps: number;
  tx_bps: number;
}

export interface DeviceStatusMessage {
  type: "device_status";
  devices: DeviceStatusUpdate[];
}

export interface PortMetricsMessage {
  type: "port_metrics";
  ports: PortMetricUpdate[];
}

export interface TopologyChangedMessage {
  type: "topology_changed";
}

export interface AlertsChangedMessage {
  type: "alerts_changed";
}

export interface SecurityFindingsChangedMessage {
  type: "security_findings_changed";
}

export type SocketMessage =
  | DeviceStatusMessage
  | PortMetricsMessage
  | TopologyChangedMessage
  | AlertsChangedMessage
  | SecurityFindingsChangedMessage;

export interface Alert {
  id: number;
  device_id: number;
  rule_type: string;
  severity: "warning" | "critical";
  message: string;
  created_at: string;
  resolved_at: string | null;
}

export interface Activity {
  id: number;
  device_id: number | null;
  event_type: string;
  message: string;
  created_at: string;
}

export interface MetricSample {
  ts: string;
  value: number;
}

export type MetricRange = "15m" | "1h" | "6h" | "24h" | "7d";

export type FindingSeverity = "low" | "medium" | "high" | "critical";

export interface SecurityFinding {
  id: number;
  device_id: number;
  finding_type: "insecure_service" | "weak_snmp_credential";
  port: number | null;
  service_name: string;
  banner: string | null;
  severity: FindingSeverity;
  title: string;
  detail: string;
  remediation: string;
  first_seen: string;
  last_seen: string;
  resolved_at: string | null;
  acknowledged_at: string | null;
}

export interface SecurityOverview {
  network_score: number;
  critical_count: number;
  high_count: number;
  medium_count: number;
  low_count: number;
  devices_scanned: number;
  last_scan_at: string | null;
}
