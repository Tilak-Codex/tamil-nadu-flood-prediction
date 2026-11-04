import React, { useState, useEffect } from 'react';
import {
  Building2,
  Waves,
  MapPin,
  Calendar,
  AlertTriangle,
  TrendingUp,
  BrainCircuit,
  ShieldCheck,
  RefreshCw
} from 'lucide-react';
import { fetchForecast, runPrediction } from '../api';

export default function StationDetails({
  stations = [],
  selectedStationId,
  onSelectStation,
  onNavigateTab,
}) {
  const [stationId, setStationId] = useState(selectedStationId || 0);
  const [forecast, setForecast] = useState(null);
  const [loading, setLoading] = useState(false);
  const [running, setRunning] = useState(false);

  useEffect(() => {
    if (selectedStationId !== undefined) {
      setStationId(selectedStationId);
    }
  }, [selectedStationId]);

  useEffect(() => {
    loadForecast(stationId);
  }, [stationId]);

  const loadForecast = async (id) => {
    setLoading(true);
    try {
      const data = await fetchForecast(id);
      setForecast(data);
    } catch (err) {
      console.error('Failed to load forecast:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleRunInference = async () => {
    setRunning(true);
    try {
      const data = await runPrediction(stationId);
      setForecast(data);
    } catch (err) {
      console.error('Inference trigger failed:', err);
    } finally {
      setRunning(false);
    }
  };

  const stn = stations.find((s) => s.station_id === stationId) || stations[0] || {};

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
      {/* Station Selector Bar */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="flex items-center gap-3 w-full sm:w-auto">
          <Building2 className="w-5 h-5 text-blue-400 shrink-0" />
          <div className="w-full sm:w-auto">
            <label className="text-xs text-slate-400 block mb-1">Select Monitoring Station:</label>
            <select
              value={stationId}
              onChange={(e) => {
                const id = parseInt(e.target.value, 10);
                setStationId(id);
                onSelectStation(id);
              }}
              className="bg-slate-950 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-white focus:outline-none focus:border-blue-500 font-medium"
            >
              {stations.map((s) => (
                <option key={s.station_id} value={s.station_id}>
                  [{s.station_id}] {s.station_name} — River {s.river} ({s.basin})
                </option>
              ))}
            </select>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => onNavigateTab('charts')}
            className="px-3 py-1.5 text-xs bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 rounded-lg font-medium transition"
          >
            View Hydrograph
          </button>
          <button
            onClick={handleRunInference}
            disabled={running}
            className="px-3 py-1.5 text-xs bg-blue-600 hover:bg-blue-500 text-white rounded-lg font-medium flex items-center gap-1.5 transition disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${running ? 'animate-spin' : ''}`} />
            <span>{running ? 'Computing LSTM...' : 'Re-run Model Prediction'}</span>
          </button>
        </div>
      </div>

      {/* Main Details Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: Station Attributes */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4">
          <h3 className="text-sm font-semibold text-white border-b border-slate-800 pb-3 flex items-center gap-2">
            <MapPin className="w-4 h-4 text-blue-400" />
            Station Geographic Attributes
          </h3>

          <div className="space-y-3 text-xs">
            <div className="flex justify-between py-1 border-b border-slate-800/60">
              <span className="text-slate-400">Station Name:</span>
              <span className="text-white font-semibold">{stn.station_name}</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-800/60">
              <span className="text-slate-400">Station ID:</span>
              <span className="text-slate-200">{stn.station_id}</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-800/60">
              <span className="text-slate-400">River:</span>
              <span className="text-slate-200">{stn.river}</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-800/60">
              <span className="text-slate-400">Basin:</span>
              <span className="text-slate-200">{stn.basin}</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-800/60">
              <span className="text-slate-400">Latitude:</span>
              <span className="text-slate-200">{stn.latitude ? stn.latitude.toFixed(4) : 'N/A'}</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-800/60">
              <span className="text-slate-400">Longitude:</span>
              <span className="text-slate-200">{stn.longitude ? stn.longitude.toFixed(4) : 'N/A'}</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-800/60">
              <span className="text-slate-400">Zero Gauge RL:</span>
              <span className="text-slate-200">{stn.rl_zero_gauge ? `${stn.rl_zero_gauge} m` : '0.00 m'}</span>
            </div>
            <div className="flex justify-between py-1">
              <span className="text-slate-400">Mean Sea Level:</span>
              <span className="text-slate-200">{stn.mean_sea_level ? `${stn.mean_sea_level} m` : 'N/A'}</span>
            </div>
          </div>

          <div className="pt-2 border-t border-slate-800">
            <span className="text-[11px] text-slate-400">Data Origin:</span>
            <span className="ml-2 px-2 py-0.5 bg-emerald-950 text-emerald-300 border border-emerald-800 rounded text-[10px] font-semibold">
              LIVE CWC TELEMETRY STREAM
            </span>
          </div>
        </div>

        {/* Center: Live Water Level & Forecast */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4">
          <h3 className="text-sm font-semibold text-white border-b border-slate-800 pb-3 flex items-center gap-2">
            <BrainCircuit className="w-4 h-4 text-emerald-400" />
            Telemetry & Deep Learning Forecast
          </h3>

          <div className="grid grid-cols-2 gap-3">
            <div className="bg-slate-950/70 border border-slate-800 p-3.5 rounded-lg space-y-1">
              <span className="text-slate-400 text-[11px]">Latest Observed Level</span>
              <div className="text-2xl font-bold text-white">
                {forecast ? `${forecast.latest_observed_level_m.toFixed(2)} m` : 'Loading...'}
              </div>
              <div className="text-[10px] text-slate-400">
                {forecast?.observation_timestamp ? new Date(forecast.observation_timestamp).toLocaleString() : 'Recent timestamp'}
              </div>
            </div>

            <div className="bg-slate-950/70 border border-slate-800 p-3.5 rounded-lg space-y-1">
              <span className="text-slate-400 text-[11px]">Next-Hour Forecast (+1h)</span>
              <div className="text-2xl font-bold text-blue-400">
                {forecast ? `${forecast.predicted_water_level_m.toFixed(2)} m` : 'Loading...'}
              </div>
              <div className="text-[10px] text-blue-300/80">
                LSTM Embedding Model
              </div>
            </div>
          </div>

          <div className="bg-slate-950/50 border border-slate-800/80 rounded-lg p-3 space-y-2 text-xs">
            <div className="flex justify-between items-center">
              <span className="text-slate-400">Rate of Water Rise:</span>
              <span className={`font-semibold ${forecast?.rate_of_change_m_per_h > 0 ? 'text-amber-400' : 'text-slate-300'}`}>
                {forecast ? `${forecast.rate_of_change_m_per_h >= 0 ? '+' : ''}${forecast.rate_of_change_m_per_h.toFixed(3)} m/h` : '0.000 m/h'}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-slate-400">Forecast Horizon:</span>
              <span className="text-slate-300 font-medium">1 Hour Ahead (Lookback: 24h)</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-slate-400">Input Feature Dimensions:</span>
              <span className="text-slate-300 font-medium">4 (Water Level, Rain, Temp, Press)</span>
            </div>
          </div>

          <div className="p-3 rounded-lg border border-slate-800 bg-slate-950/70">
            <div className="flex items-center justify-between mb-1.5">
              <span className="text-xs text-slate-400">Evaluated Severity Category:</span>
              <span className={`px-2.5 py-0.5 text-xs font-bold rounded border ${getSeverityBadge(forecast?.severity || forecast?.risk_level)}`}>
                {forecast?.severity || forecast?.risk_level || 'Loading...'}
              </span>
            </div>
            <p className="text-xs text-slate-300">{forecast?.severity_reason || forecast?.risk_reason}</p>
          </div>
        </div>

        {/* Right: CWC Thresholds & Action Advisory */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4">
          <h3 className="text-sm font-semibold text-white border-b border-slate-800 pb-3 flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-amber-400" />
            CWC Thresholds & Civil Defense
          </h3>

          <div className="space-y-2.5 text-xs">
            <div className="flex justify-between items-center p-2 rounded bg-slate-950/70 border border-slate-800/80">
              <span className="text-amber-300 font-medium">CWC Warning Level:</span>
              <strong className="text-amber-400">{stn.warning_level ? `${stn.warning_level} m` : 'UNAVAILABLE'}</strong>
            </div>
            <div className="flex justify-between items-center p-2 rounded bg-slate-950/70 border border-slate-800/80">
              <span className="text-red-300 font-medium">CWC Danger Level:</span>
              <strong className="text-red-400">{stn.danger_level ? `${stn.danger_level} m` : 'UNAVAILABLE'}</strong>
            </div>
            <div className="flex justify-between items-center p-2 rounded bg-slate-950/70 border border-slate-800/80">
              <span className="text-purple-300 font-medium">Highest Flood Level (HFL):</span>
              <strong className="text-purple-400">{stn.hfl ? `${stn.hfl} m` : 'UNAVAILABLE'}</strong>
            </div>
          </div>

          <div className="p-3 bg-blue-950/30 border border-blue-900/40 rounded-lg space-y-1.5">
            <span className="text-xs font-semibold text-blue-300 block">Civil Defense Action Advisory:</span>
            <p className="text-xs text-slate-300">{forecast?.action_recommendation || 'Maintain normal hydrologic telemetry inspection.'}</p>
          </div>

          <div className="text-[11px] text-slate-400 italic">
            {forecast?.disclaimer || 'Advisory notice for research decision support.'}
          </div>
        </div>
      </div>
    </div>
  );
}
