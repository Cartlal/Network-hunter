import { useEffect, useState } from "react";
import { fetchActivity } from "../api/client";
import type { Activity } from "../types";
import { formatRelativeTime } from "../utils/time";

const DOT_CLASS: Record<string, string> = {
  connected: "online",
  alert_resolved: "online",
  disconnected: "offline",
  alert: "warning",
};

export function LogsPage() {
  const [activity, setActivity] = useState<Activity[]>([]);

  useEffect(() => {
    fetchActivity(200).then(setActivity);
    const interval = setInterval(() => fetchActivity(200).then(setActivity), 15000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="page-scroll">
      <div className="topology-header">
        <strong>Logs</strong>
      </div>
      <div className="list-panel">
        {activity.length === 0 ? (
          <div className="empty-drawer">No activity recorded yet.</div>
        ) : (
          <div className="activity-rows full-list">
            {activity.map((item) => (
              <div className="activity-row" key={item.id}>
                <span className={`activity-dot ${DOT_CLASS[item.event_type] ?? "offline"}`} />
                <span className="activity-message">{item.message}</span>
                <span className="activity-time">{formatRelativeTime(item.created_at)}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
