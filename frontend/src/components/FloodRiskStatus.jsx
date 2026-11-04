import { useState, useEffect } from 'react';
import { AlertTriangle, CheckCircle, Minus, Info } from 'lucide-react';
import { fetchRiskSummary } from '../api';

const RISK_CONFIG = {
  Normal: { color: 'bg-green-100 border-green-300 text-green-800', icon: CheckCircle, iconColor: 'text-green-600', badge: 'bg-green-500' },
  'Above Normal': { color: 'bg-yellow-100 border-yellow-300 text-yellow-800', icon: AlertTriangle, iconColor: 'text-yellow-500', badge: 'bg-yellow-500' },
  Severe: { color: 'bg-orange-100 border-orange-300 text-orange-800', icon: AlertTriangle, iconColor: 'text-orange-500', badge: 'bg-orange-500' },
  Extreme: { color: 'bg-red-100 border-red-300 text-red-800', icon: AlertTriangle, iconColor: 'text-red-600', badge: 'bg-red-600' },
  'Threshold Unavailable': { color: 'bg-gray-100 border-gray-300 text-gray-600', icon: Minus, iconColor: 'text-gray-400', badge: 'bg-gray-400' },
};

export default function FloodRiskStatus({ stations = [], onSelectStation }) {
  const [riskData, setRiskData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    setLoading(true);
    fetchRiskSummary()
      .then(setRiskData)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="flex justify-center py-24">
        <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-600" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700 text-sm">{error}</div>
    );
  }

  const categories = Object.keys(RISK_CONFIG);
  const stationRisks = riskData?.station_risks ?? [];

  // Tally each category
  const tally = {};
  categories.forEach((c) => { tally[c] = 0; });
  stationRisks.forEach((sr) => {
    const cat = sr.risk_category ?? 'Threshold Unavailable';
    tally[cat] = (tally[cat] ?? 0) + 1;
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-xl border border-gray-200 p-4">
        <h2 className="text-lg font-bold text-gray-800">Flood Risk Status</h2>
        <p className="text-xs text-amber-600 mt-0.5">
          ⚠ Risk classifications use CWC-verified thresholds where available.
          "Threshold Unavailable" is returned when official thresholds are not on record.
        </p>
      </div>

      {/* Disclaimer */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 flex gap-2 text-xs text-blue-800">
        <Info className="w-4 h-4 flex-shrink-0 mt-0.5" />
        <span>
          Risk categories (Normal / Above Normal / Severe / Extreme) are derived from CWC Warning Level,
          Danger Level and Highest Flood Level thresholds. Only stations with verified CWC data
          are classified. Never uses arbitrary thresholds.
        </span>
      </div>

      {/* Category Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
        {categories.map((cat) => {
          const cfg = RISK_CONFIG[cat];
          const Icon = cfg.icon;
          return (
            <div key={cat} className={`rounded-xl border p-4 ${cfg.color}`}>
              <Icon className={`w-5 h-5 ${cfg.iconColor} mb-2`} />
              <p className="text-2xl font-bold">{tally[cat] ?? 0}</p>
              <p className="text-xs font-medium mt-1">{cat}</p>
            </div>
          );
        })}
      </div>

      {/* Per-station table */}
      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
        <div className="p-4 border-b border-gray-100">
          <h3 className="font-semibold text-gray-700">Station-Level Risk Assessment</h3>
          <p className="text-xs text-gray-400 mt-0.5">
            {stationRisks.length} stations · Based on latest available observations
          </p>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 text-gray-500 text-xs uppercase tracking-wide">
              <tr>
                <th className="px-4 py-3 text-left">Station</th>
                <th className="px-4 py-3 text-left">River / Basin</th>
                <th className="px-4 py-3 text-right">Water Level (m)</th>
                <th className="px-4 py-3 text-right">Warning (m)</th>
                <th className="px-4 py-3 text-right">Danger (m)</th>
                <th className="px-4 py-3 text-center">Risk Category</th>
                <th className="px-4 py-3 text-center">Threshold Source</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {stationRisks.length === 0 && (
                <tr>
                  <td colSpan={7} className="text-center py-8 text-gray-400 text-sm">
                    No risk data available. Run predictions first.
                  </td>
                </tr>
              )}
              {stationRisks.map((sr) => {
                const cat = sr.risk_category ?? 'Threshold Unavailable';
                const cfg = RISK_CONFIG[cat] ?? RISK_CONFIG['Threshold Unavailable'];
                return (
                  <tr
                    key={sr.station_id}
                    className="hover:bg-gray-50 cursor-pointer"
                    onClick={() => onSelectStation?.(sr.station_id)}
                  >
                    <td className="px-4 py-3 font-medium text-gray-800">
                      {sr.station_name ?? `Station ${sr.station_id}`}
                    </td>
                    <td className="px-4 py-3 text-gray-500">{sr.river_name ?? '—'}</td>
                    <td className="px-4 py-3 text-right">
                      {sr.current_level != null ? sr.current_level.toFixed(2) : '—'}
                    </td>
                    <td className="px-4 py-3 text-right text-amber-600">
                      {sr.warning_level != null ? sr.warning_level.toFixed(2) : '—'}
                    </td>
                    <td className="px-4 py-3 text-right text-red-600">
                      {sr.danger_level != null ? sr.danger_level.toFixed(2) : '—'}
                    </td>
                    <td className="px-4 py-3 text-center">
                      <span className={`inline-block px-2 py-0.5 rounded-full text-xs font-semibold ${cfg.color}`}>
                        {cat}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-center">
                      {sr.threshold_source === 'VERIFIED_CWC' ? (
                        <span className="text-green-600 text-xs font-medium">✅ CWC Verified</span>
                      ) : sr.threshold_source === 'DUMMY_PLACEHOLDER' ? (
                        <span className="text-gray-400 text-xs">Placeholder</span>
                      ) : (
                        <span className="text-gray-400 text-xs">—</span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Disclaimer footer */}
      <div className="text-xs text-gray-400 text-center">
        Risk classifications are for research / educational purposes only.
        Do not use for emergency response without official CWC / IMD bulletins.
      </div>
    </div>
  );
}
