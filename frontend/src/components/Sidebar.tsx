import {
  Activity,
  Bell,
  FileText,
  LayoutDashboard,
  Map,
  Network,
  Plug,
  ScrollText,
  Server,
  Settings,
  Shield,
  Users,
} from "lucide-react";
import type { Page } from "../types";

const NAV_ITEMS: { label: string; page: Page; icon: typeof LayoutDashboard }[] = [
  { label: "Security", page: "security", icon: Shield },
  { label: "Dashboard", page: "dashboard", icon: LayoutDashboard },
  { label: "Topology", page: "topology", icon: Network },
  { label: "Devices", page: "devices", icon: Server },
  { label: "Clients", page: "clients", icon: Users },
  { label: "Map", page: "map", icon: Map },
  { label: "Alerts", page: "alerts", icon: Bell },
  { label: "Performance", page: "performance", icon: Activity },
  { label: "Ports", page: "ports", icon: Plug },
  { label: "Reports", page: "reports", icon: FileText },
  { label: "Logs", page: "logs", icon: ScrollText },
  { label: "Settings", page: "settings", icon: Settings },
];

export function Sidebar({ active, onNavigate }: { active: Page; onNavigate: (page: Page) => void }) {
  return (
    <nav className="sidebar">
      <div className="sidebar-brand">
        Network Hunter
        <span>Security Posture Monitor</span>
      </div>
      {NAV_ITEMS.map(({ label, page, icon: Icon }) => (
        <div
          key={label}
          className={`sidebar-item${active === page ? " active" : ""}`}
          onClick={() => onNavigate(page)}
        >
          <Icon size={16} />
          {label}
        </div>
      ))}
    </nav>
  );
}
