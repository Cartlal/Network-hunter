import { ActivityCard } from "../components/ActivityCard";
import { AlertsCard } from "../components/AlertsCard";
import { BandwidthCard } from "../components/BandwidthCard";
import { HealthGauge } from "../components/HealthGauge";
import { SpeedTestCard } from "../components/SpeedTestCard";
import type { NetworkState } from "../hooks/useNetworkState";

export function DashboardPage({ network }: { network: NetworkState }) {
  const { topology, bandwidth, alerts, activity } = network;
  const devices = topology?.devices ?? [];

  return (
    <div className="page-scroll">
      <div className="topology-header">
        <div>
          <strong>Dashboard</strong>
          <span className="live-badge">
            <span className="live-dot" /> Live
          </span>
        </div>
      </div>
      <div className="dash-summary-row">
        <div className="summary-tile">
          <div className="summary-value">{devices.length}</div>
          <div className="summary-label">Total Devices</div>
        </div>
        <div className="summary-tile">
          <div className="summary-value">{devices.filter((d) => d.status === "online").length}</div>
          <div className="summary-label">Online</div>
        </div>
        <div className="summary-tile">
          <div className="summary-value">{alerts.filter((a) => !a.resolved_at).length}</div>
          <div className="summary-label">Active Alerts</div>
        </div>
        <div className="summary-tile">
          <div className="summary-value">{devices.filter((d) => d.snmp_supported).length}</div>
          <div className="summary-label">SNMP-Managed</div>
        </div>
      </div>
      <div className="stat-row">
        <HealthGauge devices={devices} alerts={alerts} />
        <BandwidthCard devices={devices} bandwidth={bandwidth} />
        <SpeedTestCard />
        <AlertsCard alerts={alerts} />
        <ActivityCard activity={activity} />
      </div>
    </div>
  );
}
