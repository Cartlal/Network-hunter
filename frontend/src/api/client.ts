import type {
  Activity,
  Alert,
  Device,
  MetricRange,
  MetricSample,
  Port,
  SecurityFinding,
  SecurityOverview,
  SpeedTestResult,
  Topology,
} from "../types";

async function apiFetch(path: string, options: RequestInit = {}): Promise<Response> {
  return fetch(path, options);
}

async function json<T>(res: Response): Promise<T> {
  if (!res.ok) throw new Error(`Request failed: ${res.status}`);
  return res.json();
}

function jsonBody(body: unknown): RequestInit {
  return { headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) };
}

export async function fetchTopology(): Promise<Topology> {
  return json(await apiFetch("/api/topology"));
}

export async function fetchDevicePorts(deviceId: number): Promise<Port[]> {
  return json(await apiFetch(`/api/devices/${deviceId}/ports`));
}

export async function setSnmpConfig(
  deviceId: number,
  config: { snmp_enabled: boolean; snmp_community?: string },
): Promise<Device> {
  return json(await apiFetch(`/api/devices/${deviceId}/snmp-config`, { method: "PUT", ...jsonBody(config) }));
}

export async function setDevicePosition(deviceId: number, pos_x: number, pos_y: number): Promise<Device> {
  return json(
    await apiFetch(`/api/devices/${deviceId}/position`, { method: "PUT", ...jsonBody({ pos_x, pos_y }) }),
  );
}

export async function fetchAlerts(activeOnly = false, limit = 50): Promise<Alert[]> {
  return json(await apiFetch(`/api/alerts?active_only=${activeOnly}&limit=${limit}`));
}

export async function fetchActivity(limit = 50): Promise<Activity[]> {
  return json(await apiFetch(`/api/activity?limit=${limit}`));
}

export async function fetchDeviceMetrics(
  deviceId: number,
  metricType: "latency_ms" | "rx_bps" | "tx_bps",
  range: MetricRange,
): Promise<MetricSample[]> {
  return json(await apiFetch(`/api/devices/${deviceId}/metrics?metric_type=${metricType}&range=${range}`));
}

export async function fetchAllPorts(): Promise<Port[]> {
  return json(await apiFetch("/api/ports"));
}

export async function setDeviceMapPosition(deviceId: number, map_x: number, map_y: number): Promise<Device> {
  return json(
    await apiFetch(`/api/devices/${deviceId}/map-position`, { method: "PUT", ...jsonBody({ map_x, map_y }) }),
  );
}

export async function setDeviceName(deviceId: number, custom_name: string | null): Promise<Device> {
  return json(await apiFetch(`/api/devices/${deviceId}/name`, { method: "PUT", ...jsonBody({ custom_name }) }));
}

export async function fetchSecurityOverview(): Promise<SecurityOverview> {
  return json(await apiFetch("/api/security/overview"));
}

export async function fetchSecurityFindings(includeAcknowledged = true): Promise<SecurityFinding[]> {
  return json(await apiFetch(`/api/security/findings?include_acknowledged=${includeAcknowledged}`));
}

export async function acknowledgeFinding(findingId: number): Promise<SecurityFinding> {
  return json(await apiFetch(`/api/security/findings/${findingId}/acknowledge`, { method: "POST" }));
}

export async function triggerSecurityRescan(): Promise<void> {
  await apiFetch("/api/security/rescan", { method: "POST" });
}

export async function triggerTopologyRescan(): Promise<void> {
  await apiFetch("/api/topology/rescan", { method: "POST" });
}

export async function runSpeedTest(): Promise<SpeedTestResult> {
  return json(await apiFetch("/api/speedtest/run", { method: "POST" }));
}

export async function fetchLatestSpeedTest(): Promise<SpeedTestResult | null> {
  return json(await apiFetch("/api/speedtest/latest"));
}

export async function fetchSpeedTestHistory(limit = 10): Promise<SpeedTestResult[]> {
  return json(await apiFetch(`/api/speedtest/history?limit=${limit}`));
}
