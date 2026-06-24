"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { 
  LayoutDashboard, 
  Users, 
  Calendar, 
  Trophy, 
  Menu, 
  X, 
  Activity,
  BarChart3
} from "lucide-react";

export default function Sidebar() {
  const pathname = usePathname();
  const [isOpen, setIsOpen] = useState(false);

  const menuItems = [
    { name: "儀表板首頁", path: "/", icon: LayoutDashboard },
    { name: "數據排行榜", path: "/leaderboard", icon: BarChart3 },
    { name: "分區戰績表", path: "/standings", icon: Trophy },
    { name: "所有球隊", path: "/teams", icon: Activity },
    { name: "球員名冊", path: "/players", icon: Users },
    { name: "賽程與比分", path: "/games", icon: Calendar },
  ];

  const toggleSidebar = () => setIsOpen(!isOpen);

  return (
    <>
      {/* Mobile Top Header Navbar */}
      <header className="mobile-header glass">
        <div className="mobile-logo">
          <Activity className="logo-icon animate-pulse" size={24} color="#007aff" />
          <span>MLB Analytics</span>
        </div>
        <button className="mobile-toggle" onClick={toggleSidebar} aria-label="Toggle Menu">
          {isOpen ? <X size={24} /> : <Menu size={24} />}
        </button>
      </header>

      {/* Sidebar Wrapper */}
      <aside className={`sidebar glass ${isOpen ? "open" : ""}`}>
        <div className="sidebar-brand">
          <Activity className="logo-icon" size={32} color="#007aff" />
          <div>
            <h2>MLB Analytics</h2>
            <span>2024 Season Dashboard</span>
          </div>
        </div>

        <nav className="sidebar-nav">
          <ul>
            {menuItems.map((item) => {
              const Icon = item.icon;
              const isActive = pathname === item.path;
              return (
                <li key={item.path}>
                  <Link 
                    href={item.path} 
                    className={`nav-link ${isActive ? "active" : ""}`}
                    onClick={() => setIsOpen(false)}
                  >
                    <Icon size={20} className="nav-icon" />
                    <span>{item.name}</span>
                  </Link>
                </li>
              );
            })}
          </ul>
        </nav>

        <div className="sidebar-footer">
          <div className="footer-status">
            <span className="status-indicator"></span>
            <span>API Server Online</span>
          </div>
          <p className="copyright">© 2026 MLB Platform</p>
        </div>
      </aside>

      {/* Overlay for mobile drawer */}
      {isOpen && <div className="sidebar-overlay" onClick={toggleSidebar}></div>}
    </>
  );
}
