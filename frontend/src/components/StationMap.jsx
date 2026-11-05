import React, { useState } from 'react';
import { MapContainer, TileLayer, CircleMarker, Popup, Tooltip } from 'react-leaflet';
import { Filter, Search } from 'lucide-react';
import { getRiskCategory } from './riskCategories';

export default function StationMap({
  stations = [],
  mapSummary = [],
  onSelectStation,
  onNavigateTab,
}) {
  const [selectedBasin, setSelectedBasin] = useState('ALL');
  const [searchQuery, setSearchQuery] = useState('');

  // Merge map summary predictions with stations
  const mergedStations = stations.map((stn) => {
    const summary = mapSummary.find((m) => m.station_id === stn.station_id) || {};
    return {
      ...stn,
      ...summary,
      latitude: summary.latitude || stn.latitude,
      longitude: summary.longitude || stn.longitude,
      severity: getRiskCategory(summary),
      severity_color: summary.severity_color || '#64748b',
      latest_observed_level_m: summary.latest_observed_level_m,
      predicted_water_level_m: summary.predicted_water_level_m,
    };
  });

  const basins = ['ALL', ...new Set(stations.map((s) => s.basin).filter(Boolean))];

  const filteredStations = mergedStations.filter((s) => {
    const matchesBasin = selectedBasin === 'ALL' || s.basin === selectedBasin;
    const matchesSearch =
      searchQuery === '' ||
      s.station_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (s.river && s.river.toLowerCase().includes(searchQuery.toLowerCase()));
    return matchesBasin && matchesSearch && s.latitude && s.longitude;
  });

  const getMarkerColor = (sev) => {
    switch (sev) {
      case 'Extreme':
        return '#ef4444'; // Red
      case 'Severe':
        return '#f97316'; // Orange
      case 'Above Normal':
        return '#eab308'; // Yellow
      case 'Normal':
        return '#10b981'; // Green
      default:
        return '#64748b'; // Slate gray
    }
  };

  return (
    <div className="space-y-4">
      {/* Filters and Search Bar */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 flex flex-col md:flex-row items-center justify-between gap-4">
        <div className="flex items-center gap-2 w-full md:w-auto">
          <div className="relative w-full md:w-64">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
            <input
              type="text"
              placeholder="Search station or river..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-slate-950 border border-slate-700 rounded-lg pl-9 pr-3 py-1.5 text-xs text-white placeholder-slate-400 focus:outline-none focus:border-blue-500"
            />
          </div>

          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-slate-400 shrink-0" />
            <select
              value={selectedBasin}
              onChange={(e) => setSelectedBasin(e.target.value)}
              className="bg-slate-950 border border-slate-700 rounded-lg px-2.5 py-1.5 text-xs text-white focus:outline-none focus:border-blue-500"
            >
              {basins.map((b) => (
                <option key={b} value={b}>
                  {b === 'ALL' ? 'All River Basins' : b}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Legend */}
        <div className="flex flex-wrap items-center gap-3 text-xs text-slate-300">
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-500"></span>
            <span>Normal</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-amber-500"></span>
            <span>Above Normal</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-orange-500"></span>
            <span>Severe</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-red-500"></span>
            <span>Extreme</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-slate-500"></span>
            <span>Unavailable</span>
          </div>
        </div>
      </div>

      {/* Leaflet Map Card */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-3 shadow-sm h-[600px] relative">
        <MapContainer
          center={[11.1271, 78.6569]}
          zoom={7}
          scrollWheelZoom={true}
          className="h-full w-full rounded-lg"
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />

          {filteredStations.map((stn) => {
            const color = getMarkerColor(stn.severity);
            return (
              <CircleMarker
                key={stn.station_id}
                center={[stn.latitude, stn.longitude]}
                radius={8}
                pathOptions={{
                  color: '#ffffff',
                  weight: 1.5,
                  fillColor: color,
                  fillOpacity: 0.85,
                }}
              >
                <Tooltip direction="top" offset={[0, -8]} opacity={1}>
                  <span className="font-semibold">{stn.station_name}</span> ({stn.severity})
                </Tooltip>

                <Popup>
                  <div className="p-1 space-y-2 text-xs">
                    <div className="border-b pb-1 font-bold text-slate-900 text-sm">
                      {stn.station_name}
                    </div>
                    <div className="text-slate-700 space-y-0.5">
                      <div>River: <strong>{stn.river}</strong></div>
                      <div>Basin: <strong>{stn.basin}</strong></div>
                      <div>Status: <span style={{ color: color, fontWeight: 'bold' }}>{stn.severity}</span></div>
                    </div>

                    <div className="bg-slate-100 p-2 rounded space-y-1">
                      <div>Observed: <strong>{stn.latest_observed_level_m !== undefined ? `${stn.latest_observed_level_m.toFixed(2)} m` : 'Loading...'}</strong></div>
                      <div>Predicted (+1h): <strong className="text-blue-700">{stn.predicted_water_level_m !== undefined ? `${stn.predicted_water_level_m.toFixed(2)} m` : 'Loading...'}</strong></div>
                    </div>

                    <div className="text-[11px] text-slate-500 space-y-0.5">
                      <div>Warning Level: {stn.warning_level ? `${stn.warning_level} m` : 'Unavailable'}</div>
                      <div>Danger Level: {stn.danger_level ? `${stn.danger_level} m` : 'Unavailable'}</div>
                    </div>

                    <button
                      onClick={() => {
                        onSelectStation(stn.station_id);
                        onNavigateTab('details');
                      }}
                      className="w-full mt-2 bg-blue-600 hover:bg-blue-700 text-white font-medium py-1 px-2 rounded text-xs transition"
                    >
                      View Hydrograph & Inferences
                    </button>
                  </div>
                </Popup>
              </CircleMarker>
            );
          })}
        </MapContainer>
      </div>
    </div>
  );
}
