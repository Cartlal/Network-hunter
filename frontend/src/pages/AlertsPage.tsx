import { AlertTriangle, CheckCircle2, ShieldAlert } from "lucide-react";
import { useEffect, useState } from "react";
import { fetchAlerts } from "../api/client";
import type { Alert } from "../types";
import { formatRelativeTime } from "../utils/time";

export function AlertsPage() {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [activeOnly, setActiveOnly] = useState(true);

  useEffect(() => {
    fetchAlerts(activeOnly, 200).then(setAlerts);
  }, [activeOnly]);

  return (
    <div className="page-scroll">
      <div className="topology-header">
        <strong>Alerts</strong>
        <div className="range-selector" style={{ marginLeft: "auto" }}>
          <button className={`range-btn${activeOnly ? " active" : ""}`} onClick={() => setActiveOnly(true)}>
            Active
          </button>
          <button className={`range-btn${!activeOnly ? " active" : ""}`} onClick={() => setActiveOnly(false)}>
            All
          </button>
        </div>
      </div>
      <div className="list-panel">
        {alerts.length === 0 ? (
          <div className="empty-drawer">No {activeOnly ? "active" : ""} alerts.</div>
        ) : (
          <div className="alert-rows full-list">
            {alerts.map((alert) => {
              const Icon = alert.resolved_at ? CheckCircle2 : alert.severity === "critical" ? ShieldAlert : AlertTriangle;
              return (
                <div className="alert-row" key={alert.id}>
                  <Icon size={18} className={`alert-icon ${alert.resolved_at ? "online" : alert.severity}`} />
                  <div className="alert-body">
                    <div className="alert-message">{alert.message}</div>
                    <div className="alert-time">
                      {alert.resolved_at
                        ? `Resolved ${formatRelativeTime(alert.resolved_at)}`
                        : `Raised ${formatRelativeTime(alert.created_at)}`}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
