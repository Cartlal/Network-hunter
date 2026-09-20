import { useState } from "react";
import { Sidebar } from "./components/Sidebar";
import { TopBar } from "./components/TopBar";
import { useNetworkState } from "./hooks/useNetworkState";
import { AlertsPage } from "./pages/AlertsPage";
import { ClientsPage } from "./pages/ClientsPage";
import { DashboardPage } from "./pages/DashboardPage";
import { DevicesPage } from "./pages/DevicesPage";
import { LogsPage } from "./pages/LogsPage";
import { MapPage } from "./pages/MapPage";
import { PerformancePage } from "./pages/PerformancePage";
import { PortsPage } from "./pages/PortsPage";
import { ReportsPage } from "./pages/ReportsPage";
import { SecurityPage } from "./pages/SecurityPage";
import { SettingsPage } from "./pages/SettingsPage";
import { TopologyPage } from "./pages/TopologyPage";
import type { Page } from "./types";

export default function App() {
  const [page, setPage] = useState<Page>("security");
  const network = useNetworkState();

  return (
    <div className="app-shell">
      <Sidebar active={page} onNavigate={setPage} />
      <main className="main-content">
        <TopBar />
        {page === "security" && <SecurityPage network={network} />}
        {page === "dashboard" && <DashboardPage network={network} />}
        {page === "topology" && <TopologyPage network={network} />}
        {page === "devices" && <DevicesPage network={network} />}
        {page === "clients" && <ClientsPage network={network} />}
        {page === "map" && <MapPage network={network} />}
        {page === "alerts" && <AlertsPage />}
        {page === "performance" && <PerformancePage network={network} />}
        {page === "ports" && <PortsPage network={network} />}
        {page === "reports" && <ReportsPage network={network} />}
        {page === "logs" && <LogsPage />}
        {page === "settings" && <SettingsPage network={network} />}
      </main>
    </div>
  );
}
