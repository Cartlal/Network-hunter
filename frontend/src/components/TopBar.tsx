import { Search } from "lucide-react";

export function TopBar() {
  return (
    <div className="topbar">
      <div className="topbar-search">
        <Search size={16} />
        <input placeholder="Search devices, IP, MAC, hostname..." />
      </div>
    </div>
  );
}
