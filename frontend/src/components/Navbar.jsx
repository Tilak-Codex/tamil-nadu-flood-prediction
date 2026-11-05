import React from 'react';
import {
  LayoutDashboard,
  MapPin,
  ShieldAlert,
  Bell,
  Waves
} from 'lucide-react';

export default function Navbar({ activeTab, onTabChange, alertCount = 0 }) {
  const setActiveTab = onTabChange;
  const navItems = [
    { id: 'overview', label: 'Overview', icon: LayoutDashboard },
    { id: 'map', label: 'Station Map', icon: MapPin },
    { id: 'risk', label: 'Flood Risk Status', icon: ShieldAlert },
    { id: 'alerts', label: 'Alerts', icon: Bell, badge: alertCount },
  ];

  return (
    <header className="bg-slate-900 border-b border-slate-800 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center gap-3">
            <div className="bg-blue-600 p-2 rounded-lg text-white shadow-md shadow-blue-500/20">
              <Waves className="w-6 h-6" />
            </div>
            <div>
              <span className="text-lg font-bold text-white tracking-tight">TN Flood Decision Support</span>
              <span className="hidden sm:inline-block ml-2 px-2 py-0.5 text-xs bg-blue-900/60 text-blue-300 border border-blue-700/50 rounded-full font-medium">
                Tamil Nadu CWC AI
              </span>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <div className="flex items-center gap-2 bg-emerald-950/60 border border-emerald-800/60 text-emerald-300 text-xs px-3 py-1.5 rounded-full font-medium">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
              <span>FastAPI Operational</span>
            </div>
          </div>
        </div>

        {/* Navigation Tabs */}
        <nav className="flex space-x-1 overflow-x-auto pb-2 scrollbar-none">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`flex items-center gap-2 px-3.5 py-2 text-xs sm:text-sm font-medium rounded-lg whitespace-nowrap transition-all ${
                  isActive
                    ? 'bg-blue-600 text-white shadow-sm shadow-blue-500/20'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/80'
                }`}
              >
                <Icon className="w-4 h-4" />
                <span>{item.label}</span>
                {item.badge > 0 && (
                  <span className="ml-1 px-1.5 py-0.2 bg-red-500 text-white rounded-full text-xs font-bold animate-bounce">
                    {item.badge}
                  </span>
                )}
              </button>
            );
          })}
        </nav>
      </div>
    </header>
  );
}
