import { AlertTriangle, ShieldAlert } from "lucide-react";
import type { Alert } from "../types";
import { formatRelativeTime } from "../utils/time";

export function AlertsCard({ alerts }: { alerts: Alert[] }) {
  const active = alerts.filter((a) => !a.resolved_at).slice(0, 5);

  return (
    <div className="stat-card">
      <div className="stat-card-header">
        <strong>Alerts</strong>
        <span className="view-all">View All</span>
      </div>
      {active.length === 0 ? (
        <div className="empty-drawer">No active alerts. Network looks healthy.</div>
      ) : (
        <div className="alert-rows">
          {active.map((alert) => {
            const Icon = alert.severity === "critical" ? ShieldAlert : AlertTriangle;
            return (
              <div className="alert-row" key={alert.id}>
                <Icon size={18} className={`alert-icon ${alert.severity}`} />
                <div className="alert-body">
                  <div className="alert-message">{alert.message}</div>
                  <div className="alert-time">{formatRelativeTime(alert.created_at)}</div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
