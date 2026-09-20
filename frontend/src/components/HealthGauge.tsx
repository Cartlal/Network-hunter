import type { Alert, Device } from "../types";

const RADIUS = 52;
const CIRCUMFERENCE = 2 * Math.PI * RADIUS;

function statusLabel(pct: number): { label: string; color: string } {
  if (pct >= 90) return { label: "Good", color: "var(--online)" };
  if (pct >= 70) return { label: "Warning", color: "var(--warning)" };
  return { label: "Critical", color: "var(--offline)" };
}

export function HealthGauge({ devices, alerts }: { devices: Device[]; alerts: Alert[] }) {
  const total = devices.length || 1;
  const offline = devices.filter((d) => d.status === "offline").length;
  const warningDeviceIds = new Set(
    alerts.filter((a) => !a.resolved_at && a.rule_type !== "device_down").map((a) => a.device_id),
  );
  const warning = devices.filter((d) => d.status === "online" && warningDeviceIds.has(d.id)).length;
  const online = devices.length - offline;

  const pct = Math.round((online / total) * 100);
  const { label, color } = statusLabel(pct);
  const dashOffset = CIRCUMFERENCE * (1 - pct / 100);

  return (
    <div className="stat-card health-card">
      <div className="stat-card-header">
        <strong>Network Health</strong>
      </div>
      <div className="health-gauge">
        <svg width={130} height={130} viewBox="0 0 130 130">
          <circle cx={65} cy={65} r={RADIUS} fill="none" stroke="#16203a" strokeWidth={10} />
          <circle
            cx={65}
            cy={65}
            r={RADIUS}
            fill="none"
            stroke={color}
            strokeWidth={10}
            strokeLinecap="round"
            strokeDasharray={CIRCUMFERENCE}
            strokeDashoffset={dashOffset}
            transform="rotate(-90 65 65)"
          />
        </svg>
        <div className="health-gauge-label">
          <div className="health-pct">{pct}%</div>
          <div className="health-status" style={{ color }}>
            {label}
          </div>
        </div>
      </div>
      <div className="health-counts">
        <div>
          <span className="legend-dot download" style={{ background: "var(--online)" }} />
          {online} Online
        </div>
        <div>
          <span className="legend-dot" style={{ background: "var(--offline)" }} />
          {offline} Offline
        </div>
        <div>
          <span className="legend-dot" style={{ background: "var(--warning)" }} />
          {warning} Warning
        </div>
      </div>
    </div>
  );
}
