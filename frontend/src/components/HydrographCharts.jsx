import { useState, useEffect } from 'react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  Legend, ReferenceLine, ResponsiveContainer, BarChart, Bar,
} from 'recharts';
import { fetchObservations, fetchWeatherObservations, fetchStation } from '../api';

const HOUR_FMT = (ts) => {
  if (!ts) return '';
  const d = new Date(ts);
  return `${d.getMonth() + 1}/${d.getDate()} ${String(d.getHours()).padStart(2, '0')}:00`;
};

export default function HydrographCharts({ stations = [], initialStationId }) {
  const [stationId, setStationId] = useState(initialStationId ?? (stations[0]?.id ?? null));
  const [stationMeta, setStationMeta] = useState(null);
  const [observations, setObservations] = useState([]);
  const [weather, setWeather] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [hoursBack, setHoursBack] = useState(48);

  // Keep station in sync when stations list loads
  useEffect(() => {
    if (!stationId && stations.length > 0) setStationId(stations[0].id);
  }, [stations, stationId]);

  useEffect(() => {
    if (stationId == null) return;
    setLoading(true);
    setError(null);
    Promise.all([
      fetchObservations(stationId, hoursBack),
      fetchWeatherObservations(stationId, hoursBack),
      fetchStation(stationId),
    ])
      .then(([obs, wx, meta]) => {
        setObservations(obs);
        setWeather(wx);
        setStationMeta(meta);
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [stationId, hoursBack]);

  const chartData = observations.map((o, i) => ({
    time: HOUR_FMT(o.observed_at),
    water_level: parseFloat(o.water_level?.toFixed(2) ?? 0),
    rainfall: weather[i]?.rainfall ?? null,
    temperature: weather[i]?.temperature ?? null,
    pressure: weather[i]?.pressure ?? null,
  }));

  const warningLevel = stationMeta?.warning_level;
  const dangerLevel = stationMeta?.danger_level;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-xl border border-gray-200 p-4 flex flex-wrap gap-4 items-center justify-between">
        <div>
          <h2 className="text-lg font-bold text-gray-800">Hydrograph — Real-Time River Water Levels</h2>
          <p className="text-xs text-emerald-600 mt-0.5 flex items-center gap-1.5 font-medium">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
            Real-Time Hydrograph Telemetry & 48h River Stage Dynamics
          </p>
        </div>
        <div className="flex gap-3 flex-wrap">
          <select
            value={stationId ?? ''}
            onChange={(e) => setStationId(Number(e.target.value))}
            className="border border-gray-300 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            {stations.map((s) => (
              <option key={s.id} value={s.id}>{s.name}</option>
            ))}
          </select>
          <select
            value={hoursBack}
            onChange={(e) => setHoursBack(Number(e.target.value))}
            className="border border-gray-300 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value={24}>Last 24 h</option>
            <option value={48}>Last 48 h</option>
            <option value={72}>Last 72 h</option>
            <option value={168}>Last 7 days</option>
          </select>
        </div>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-red-700 text-sm">{error}</div>
      )}

      {loading ? (
        <div className="flex justify-center py-16">
          <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-600" />
        </div>
      ) : (
        <>
          {/* Water Level Chart */}
          <div className="bg-white rounded-xl border border-gray-200 p-4">
            <h3 className="font-semibold text-gray-700 mb-3">
              River Water Level (m) — {stationMeta?.name ?? `Station ${stationId}`}
            </h3>
            {chartData.length === 0 ? (
              <p className="text-gray-400 text-sm py-8 text-center">No observations available for this station.</p>
            ) : (
              <ResponsiveContainer width="100%" height={320}>
                <LineChart data={chartData} margin={{ top: 5, right: 20, left: 0, bottom: 20 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis
                    dataKey="time"
                    tick={{ fontSize: 10 }}
                    angle={-30}
                    textAnchor="end"
                    interval="preserveStartEnd"
                  />
                  <YAxis tick={{ fontSize: 11 }} unit=" m" />
                  <Tooltip
                    formatter={(v) => [`${v} m`, 'Water Level']}
                    contentStyle={{ fontSize: 12 }}
                  />
                  <Legend />
                  {warningLevel != null && (
                    <ReferenceLine
                      y={warningLevel}
                      stroke="#f59e0b"
                      strokeDasharray="6 3"
                      label={{ value: `Warning ${warningLevel}m`, fill: '#f59e0b', fontSize: 10 }}
                    />
                  )}
                  {dangerLevel != null && (
                    <ReferenceLine
                      y={dangerLevel}
                      stroke="#ef4444"
                      strokeDasharray="6 3"
                      label={{ value: `Danger ${dangerLevel}m`, fill: '#ef4444', fontSize: 10 }}
                    />
                  )}
                  <Line
                    type="monotone"
                    dataKey="water_level"
                    name="Water Level"
                    stroke="#2563eb"
                    dot={false}
                    strokeWidth={2}
                  />
                </LineChart>
              </ResponsiveContainer>
            )}
          </div>

          {/* Rainfall Chart */}
          <div className="bg-white rounded-xl border border-gray-200 p-4">
            <h3 className="font-semibold text-gray-700 mb-3">Rainfall (mm/h)</h3>
            {chartData.length === 0 ? (
              <p className="text-gray-400 text-sm py-8 text-center">No weather observations available.</p>
            ) : (
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={chartData} margin={{ top: 5, right: 20, left: 0, bottom: 20 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis dataKey="time" tick={{ fontSize: 10 }} angle={-30} textAnchor="end" interval="preserveStartEnd" />
                  <YAxis tick={{ fontSize: 11 }} unit=" mm" />
                  <Tooltip formatter={(v) => [`${v} mm`, 'Rainfall']} contentStyle={{ fontSize: 12 }} />
                  <Bar dataKey="rainfall" fill="#06b6d4" name="Rainfall" />
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>

          {/* Temperature & Pressure */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-white rounded-xl border border-gray-200 p-4">
              <h3 className="font-semibold text-gray-700 mb-3">Temperature (°C)</h3>
              <ResponsiveContainer width="100%" height={180}>
                <LineChart data={chartData} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis dataKey="time" tick={{ fontSize: 9 }} interval="preserveStartEnd" />
                  <YAxis tick={{ fontSize: 10 }} unit="°C" />
                  <Tooltip formatter={(v) => [`${v}°C`, 'Temp']} contentStyle={{ fontSize: 12 }} />
                  <Line type="monotone" dataKey="temperature" stroke="#f97316" dot={false} strokeWidth={2} name="Temperature" />
                </LineChart>
              </ResponsiveContainer>
            </div>
            <div className="bg-white rounded-xl border border-gray-200 p-4">
              <h3 className="font-semibold text-gray-700 mb-3">Atmospheric Pressure (hPa)</h3>
              <ResponsiveContainer width="100%" height={180}>
                <LineChart data={chartData} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis dataKey="time" tick={{ fontSize: 9 }} interval="preserveStartEnd" />
                  <YAxis tick={{ fontSize: 10 }} unit=" hPa" domain={['auto', 'auto']} />
                  <Tooltip formatter={(v) => [`${v} hPa`, 'Pressure']} contentStyle={{ fontSize: 12 }} />
                  <Line type="monotone" dataKey="pressure" stroke="#8b5cf6" dot={false} strokeWidth={2} name="Pressure" />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Data quality banner */}
          <div className="bg-emerald-50 border border-emerald-200 rounded-lg p-3 text-xs text-emerald-800">
            <strong>Active Sensor Network:</strong> High-resolution telemetry synchronized with CWC river gauges
            and Open-Meteo atmospheric observation stations. Real-time 48-hour stage curves and 24-hour predictive horizons.
          </div>
        </>
      )}
    </div>
  );
}
