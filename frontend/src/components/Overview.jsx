import React from 'react';
import {
  ShieldAlert,
  Building2,
  Waves,
  Bell,
  CheckCircle2,
  AlertTriangle,
  TrendingUp,
  Cpu,
  ArrowRight
} from 'lucide-react';

export default function Overview({
  stats,
  alerts,
  stations,
  onSelectStation,
  onNavigateTab,
  onAcknowledgeAlert,
}) {
  const getSeverityBadge = (sev) => {
    switch (sev) {
      case 'Extreme':
        return 'bg-red-950/80 text-red-300 border-red-800';
      case 'Severe':
        return 'bg-orange-950/80 text-orange-300 border-orange-800';
      case 'Above Normal':
        return 'bg-amber-950/80 text-amber-300 border-amber-800';
      case 'Normal':
        return 'bg-emerald-950/80 text-emerald-300 border-emerald-800';
      default:
        return 'bg-slate-800 text-slate-300 border-slate-700';
    }
  };

  return (
    <div className="space-y-6">
      {/* Disclaimer Banner */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 flex items-start gap-3">
        <ShieldAlert className="w-5 h-5 text-blue-400 mt-0.5 shrink-0" />
        <div className="text-xs text-slate-300">
          <span className="font-semibold text-white">Academic Decision Support Prototype:</span> Computes 1-hour ahead river water-level forecasts using deep LSTM networks with station entity embeddings. Official evacuation and flood emergency directives are issued strictly by Central Water Commission (CWC) and Tamil Nadu State Disaster Management Authority (TNSDMA).
        </div>
      </div>

      {/* Top Metric Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>Monitoring Stations</span>
            <Building2 className="w-4 h-4 text-blue-400" />
          </div>
          <div className="mt-2 text-2xl font-bold text-white">{stats?.total_stations || 35}</div>
          <div className="mt-1 text-xs text-slate-400">Cauvery, Adyar, Gundar Basins</div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>Active Flood Alerts</span>
            <Bell className="w-4 h-4 text-red-400" />
          </div>
          <div className="mt-2 text-2xl font-bold text-red-400">{stats?.active_alerts || 0}</div>
          <div className="mt-1 text-xs text-red-300/80 font-medium">Exceeding CWC threshold levels</div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>Critical / Extreme</span>
            <AlertTriangle className="w-4 h-4 text-amber-400" />
          </div>
          <div className="mt-2 text-2xl font-bold text-amber-300">{stats?.critical_danger_count || 0}</div>
          <div className="mt-1 text-xs text-slate-400">Above CWC Danger Level</div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>LSTM Forecast Model</span>
            <Cpu className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="mt-2 text-2xl font-bold text-emerald-400">R² = 0.9855</div>
          <div className="mt-1 text-xs text-slate-400">NSE 0.9855 • 24h Lookback</div>
        </div>
      </div>

      {/* Grid: Risk Distribution + Active Alerts */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Risk Distribution Breakdown */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <h3 className="font-semibold text-white text-sm flex items-center gap-2">
              <ShieldAlert className="w-4 h-4 text-blue-400" />
              Statewide Risk Categories
            </h3>
            <button
              onClick={() => onNavigateTab('risk')}
              className="text-xs text-blue-400 hover:text-blue-300 flex items-center gap-1 font-medium"
            >
              Details <ArrowRight className="w-3 h-3" />
            </button>
          </div>

          <div className="space-y-3">
            {[
              { label: 'Normal', count: stats?.normal_count || 0, color: 'bg-emerald-500', text: 'text-emerald-400' },
              { label: 'Above Normal', count: stats?.severe_warning_count || 0, color: 'bg-amber-500', text: 'text-amber-400' },
              { label: 'Severe / Extreme', count: stats?.critical_danger_count || 0, color: 'bg-red-500', text: 'text-red-400' },
              { label: 'Threshold Unavailable', count: stats?.threshold_unavailable_count || 0, color: 'bg-slate-500', text: 'text-slate-400' },
            ].map((cat, idx) => (
              <div key={idx} className="flex items-center justify-between text-xs">
                <div className="flex items-center gap-2.5">
                  <span className={`w-3 h-3 rounded-full ${cat.color}`}></span>
                  <span className="text-slate-300 font-medium">{cat.label}</span>
                </div>
                <span className={`font-bold ${cat.text}`}>{cat.count} stations</span>
              </div>
            ))}
          </div>

          <div className="pt-2 border-t border-slate-800 text-[11px] text-slate-400">
            Categorization strictly checks verified CWC Warning and Danger levels per gauge. Stations without official published thresholds are classified as <span className="text-slate-300 font-semibold">Threshold Unavailable</span>.
          </div>
        </div>

        {/* Live Active Alert Stream */}
        <div className="lg:col-span-2 bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <h3 className="font-semibold text-white text-sm flex items-center gap-2">
              <Bell className="w-4 h-4 text-red-400" />
              Active Siren Alerts ({alerts?.length || 0})
            </h3>
            <button
              onClick={() => onNavigateTab('alerts')}
              className="text-xs text-blue-400 hover:text-blue-300 flex items-center gap-1 font-medium"
            >
              View All <ArrowRight className="w-3 h-3" />
            </button>
          </div>

          <div className="space-y-2.5 max-h-72 overflow-y-auto pr-1">
            {alerts && alerts.length > 0 ? (
              alerts.slice(0, 4).map((a) => (
                <div
                  key={a.id}
                  className="bg-slate-950/60 border border-slate-800 hover:border-slate-700 rounded-lg p-3 flex items-start justify-between gap-3 transition-colors"
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className={`px-2 py-0.5 text-[10px] font-bold rounded border ${getSeverityBadge(a.severity)}`}>
                        {a.severity}
                      </span>
                      <span className="text-sm font-semibold text-white">{a.station_name}</span>
                      <span className="text-xs text-slate-400">({a.river})</span>
                    </div>
                    <p className="text-xs text-slate-300">{a.message}</p>
                    <div className="text-[11px] text-slate-400 flex items-center gap-3">
                      <span>Water Level: <strong className="text-white">{a.current_water_level} m</strong></span>
                      {a.threshold_level && <span>Threshold: <strong className="text-amber-400">{a.threshold_level} m</strong></span>}
                    </div>
                  </div>

                  <button
                    onClick={() => onAcknowledgeAlert(a.id)}
                    className="px-2.5 py-1 text-xs bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 rounded font-medium shrink-0 transition"
                  >
                    Acknowledge
                  </button>
                </div>
              ))
            ) : (
              <div className="text-center py-8 text-slate-400 text-xs flex flex-col items-center gap-2">
                <CheckCircle2 className="w-8 h-8 text-emerald-400" />
                <span>No active critical alerts at this time. All monitoring gauges within normal bounds.</span>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Quick Station Grid Highlights */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm space-y-4">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <h3 className="font-semibold text-white text-sm flex items-center gap-2">
            <Waves className="w-4 h-4 text-blue-400" />
            Tamil Nadu Monitoring Stations Telemetry
          </h3>
          <button
            onClick={() => onNavigateTab('map')}
            className="text-xs text-blue-400 hover:text-blue-300 flex items-center gap-1 font-medium"
          >
            Open Interactive Map <ArrowRight className="w-3 h-3" />
          </button>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {stations && stations.slice(0, 6).map((stn) => (
            <div
              key={stn.station_id}
              onClick={() => {
                onSelectStation(stn.station_id);
                onNavigateTab('details');
              }}
              className="bg-slate-950/70 border border-slate-800/80 hover:border-blue-600/60 p-3.5 rounded-lg cursor-pointer transition-all group"
            >
              <div className="flex items-center justify-between">
                <div className="font-semibold text-sm text-white group-hover:text-blue-400 transition-colors">
                  {stn.station_name}
                </div>
                <span className="text-[10px] bg-slate-800 text-slate-300 px-2 py-0.5 rounded">
                  ID: {stn.station_id}
                </span>
              </div>
              <div className="text-xs text-slate-400 mt-1">
                River: <span className="text-slate-300">{stn.river}</span> • Basin: <span className="text-slate-300">{stn.basin}</span>
              </div>
              <div className="mt-2.5 pt-2 border-t border-slate-800/60 flex items-center justify-between text-xs">
                <span className="text-slate-400">Warning: <strong className="text-amber-400">{stn.warning_level ? `${stn.warning_level}m` : 'N/A'}</strong></span>
                <span className="text-slate-400">Danger: <strong className="text-red-400">{stn.danger_level ? `${stn.danger_level}m` : 'N/A'}</strong></span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
