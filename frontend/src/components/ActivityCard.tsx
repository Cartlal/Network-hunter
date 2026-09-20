import type { Activity } from "../types";
import { formatRelativeTime } from "../utils/time";

const DOT_CLASS: Record<string, string> = {
  connected: "online",
  alert_resolved: "online",
  disconnected: "offline",
  alert: "warning",
};

export function ActivityCard({ activity }: { activity: Activity[] }) {
  const recent = activity.slice(0, 6);

  return (
    <div className="stat-card">
      <div className="stat-card-header">
        <strong>Recent Activities</strong>
        <span className="view-all">View All</span>
      </div>
      {recent.length === 0 ? (
        <div className="empty-drawer">No activity yet.</div>
      ) : (
        <div className="activity-rows">
          {recent.map((item) => (
            <div className="activity-row" key={item.id}>
              <span className={`activity-dot ${DOT_CLASS[item.event_type] ?? "offline"}`} />
              <span className="activity-message">{item.message}</span>
              <span className="activity-time">{formatRelativeTime(item.created_at)}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
