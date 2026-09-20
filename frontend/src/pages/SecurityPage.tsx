import { RefreshCw, ShieldAlert, ShieldCheck } from "lucide-react";
import { useMemo, useState } from "react";
import { acknowledgeFinding, triggerSecurityRescan } from "../api/client";
import type { NetworkState } from "../hooks/useNetworkState";
import type { SecurityFinding } from "../types";
import { deviceName } from "../utils/deviceName";
import { formatRelativeTime } from "../utils/time";

function scoreColor(score: number): string {
  if (score >= 90) return "var(--online)";
  if (score >= 60) return "var(--warning)";
  return "var(--offline)";
}

const RADIUS = 52;
const CIRCUMFERENCE = 2 * Math.PI * RADIUS;

export function SecurityPage({ network }: { network: NetworkState }) {
  const { securityOverview, securityFindings, refreshSecurity } = network;
  const devices = network.topology?.devices ?? [];
  const [rescanning, setRescanning] = useState(false);
  const [acknowledgingId, setAcknowledgingId] = useState<number | null>(null);

  const devicesById = useMemo(() => new Map(devices.map((d) => [d.id, d])), [devices]);

  const activeFindings = securityFindings.filter((f) => !f.resolved_at && !f.acknowledged_at);
  const acknowledgedFindings = securityFindings.filter((f) => !f.resolved_at && f.acknowledged_at);

  const severityOrder: Record<string, number> = { critical: 0, high: 1, medium: 2, low: 3 };
  const sortedActive = [...activeFindings].sort((a, b) => severityOrder[a.severity] - severityOrder[b.severity]);

  const handleRescan = async () => {
    setRescanning(true);
    try {
      await triggerSecurityRescan();
      refreshSecurity();
    } finally {
      setRescanning(false);
    }
  };

  const handleAcknowledge = async (findingId: number) => {
    setAcknowledgingId(findingId);
    try {
      await acknowledgeFinding(findingId);
      refreshSecurity();
    } finally {
      setAcknowledgingId(null);
    }
  };

  const score = securityOverview?.network_score ?? 100;
  const color = scoreColor(score);
  const dashOffset = CIRCUMFERENCE * (1 - score / 100);

  const renderFinding = (finding: SecurityFinding, showAck: boolean) => {
    const device = devicesById.get(finding.device_id);
    return (
      <div className="finding-row" key={finding.id}>
        <div>
          <div className="finding-title-row">
            <span className={`severity-badge ${finding.severity}`}>{finding.severity}</span>
            <span className="finding-device">{device ? deviceName(device) : `Device #${finding.device_id}`}</span>
            <span style={{ color: "var(--text-dim)", fontSize: 12 }}>
              {device?.ip}
              {finding.port ? `:${finding.port}` : ""}
            </span>
          </div>
          <div>{finding.title}</div>
          <div className="finding-detail">{finding.detail}</div>
          <div className="finding-remediation">Fix: {finding.remediation}</div>
          {finding.banner && <span className="finding-banner">{finding.banner}</span>}
          <div className="finding-detail">Last seen {formatRelativeTime(finding.last_seen)}</div>
        </div>
        {showAck && (
          <button
            className="ack-btn"
            disabled={acknowledgingId === finding.id}
            onClick={() => handleAcknowledge(finding.id)}
          >
            {acknowledgingId === finding.id ? "Saving..." : "Acknowledge"}
          </button>
        )}
      </div>
    );
  };

  return (
    <div className="page-scroll">
      <div className="topology-header">
        <strong>Security Posture</strong>
        <button className="rescan-btn" style={{ marginLeft: "auto" }} disabled={rescanning} onClick={handleRescan}>
          <RefreshCw size={14} className={rescanning ? "spin" : ""} />
          {rescanning ? "Scanning..." : "Rescan now"}
        </button>
      </div>

      <div className="security-summary-row">
        <div className="stat-card health-card">
          <div className="stat-card-header">
            <strong>Network Score</strong>
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
              <div className="health-pct">{score}</div>
              <div className="health-status" style={{ color }}>
                {score >= 90 ? "Good" : score >= 60 ? "Needs attention" : "At risk"}
              </div>
            </div>
          </div>
        </div>
        <div className="summary-tile">
          <div className="summary-value" style={{ color: "var(--offline)" }}>
            {securityOverview?.critical_count ?? 0}
          </div>
          <div className="summary-label">Critical</div>
        </div>
        <div className="summary-tile">
          <div className="summary-value" style={{ color: "var(--warning)" }}>
            {securityOverview?.high_count ?? 0}
          </div>
          <div className="summary-label">High</div>
        </div>
        <div className="summary-tile">
          <div className="summary-value" style={{ color: "var(--accent)" }}>
            {securityOverview?.medium_count ?? 0}
          </div>
          <div className="summary-label">Medium</div>
        </div>
        <div className="summary-tile">
          <div className="summary-value">{securityOverview?.devices_scanned ?? 0}</div>
          <div className="summary-label">Devices scanned</div>
        </div>
      </div>

      <div className="list-panel">
        <h3 className="settings-section-title">Active Findings</h3>
        {sortedActive.length === 0 ? (
          <div className="empty-drawer">
            <ShieldCheck size={20} style={{ marginBottom: 6 }} />
            <div>No insecure services or weak credentials detected right now.</div>
          </div>
        ) : (
          <div>{sortedActive.map((f) => renderFinding(f, true))}</div>
        )}

        {acknowledgedFindings.length > 0 && (
          <>
            <h3 className="settings-section-title" style={{ marginTop: 20 }}>
              <ShieldAlert size={14} style={{ verticalAlign: "middle", marginRight: 6 }} />
              Acknowledged (excluded from score)
            </h3>
            <div>{acknowledgedFindings.map((f) => renderFinding(f, false))}</div>
          </>
        )}
      </div>
    </div>
  );
}
