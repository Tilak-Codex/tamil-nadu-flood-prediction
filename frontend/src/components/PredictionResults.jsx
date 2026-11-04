import { useState, useEffect } from 'react';
import {
  ComposedChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ReferenceLine, ResponsiveContainer,
  ReferenceDot,
} from 'recharts';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { fetchObservations, runPrediction } from '../api';

const HOUR_FMT = (ts) => {
  if (!ts) return '';
  const d = new Date(ts);
  return `${d.getMonth() + 1}/${d.getDate()} ${String(d.getHours()).padStart(2, '0')}:00`;
};

const RISK_COLORS = {
  Normal: 'bg-green-100 text-green-800',
  'Above Normal': 'bg-yellow-100 text-yellow-800',
  Severe: 'bg-orange-100 text-orange-800',
  Extreme: 'bg-red-100 text-red-800',
  'Threshold Unavailable': 'bg-gray-100 text-gray-600',
};

export default function PredictionResults({ stations = [], initialStationId }) {
  const [stationId, setStationId] = useState(initialStationId ?? (stations[0]?.id ?? null));
  const [observations, setObservations] = useState([]);
  const [prediction, setPrediction] = useState(null);
  const [loading, setLoading] = useState(false);
  const [predLoading, setPredLoading] = useState(false);
  const [error, setError] = useState(null);
  const [predError, setPredError] = useState(null);

  useEffect(() => {
    if (!stationId && stations.length > 0) setStationId(stations[0].id);
  }, [stations, stationId]);

  useEffect(() => {
    if (stationId == null) return;
    setLoading(true);
    setError(null);
    fetchObservations(stationId, 24)
      .then(setObservations)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [stationId]);

  const handleRunPrediction = () => {
    if (stationId == null) return;
    setPredLoading(true);
    setPredError(null);
    runPrediction(stationId)
      .then(setPrediction)
      .catch((e) => setPredError(e.message))
      .finally(() => setPredLoading(false));
  };

  // Build chart data: last 24 observations + predicted next point
  const chartData = observations.map((o) => ({
    time: HOUR_FMT(o.observed_at),
    water_level: parseFloat(o.water_level?.toFixed(2) ?? 0),
    predicted: null,
    type: 'observed',
  }));

  if (prediction?.predicted_level != null && chartData.length > 0) {
    // Add predicted point as next hour
    const lastObs = observations[observations.length - 1];
    const nextTime = lastObs?.observed_at
      ? new Date(new Date(lastObs.observed_at).getTime() + 3_600_000)
      : new Date();
    chartData.push({
      time: HOUR_FMT(nextTime.toISOString()),
      water_level: null,
      predicted: parseFloat(prediction.predicted_level.toFixed(2)),
      type: 'predicted',
    });
  }

  // Rate of change
  let trend = null;
  if (observations.length >= 2) {
    const last = observations[observations.length - 1]?.water_level;
    const prev = observations[observations.length - 2]?.water_level;
    if (last != null && prev != null) {
      const delta = last - prev;
      trend = delta > 0.05 ? 'rising' : delta < -0.05 ? 'falling' : 'stable';
    }
  }

  const trendIcon = trend === 'rising'
    ? <TrendingUp className="w-5 h-5 text-red-500" />
    : trend === 'falling'
    ? <TrendingDown className="w-5 h-5 text-green-500" />
    : <Minus className="w-5 h-5 text-gray-400" />;

  const latestLevel = observations[observations.length - 1]?.water_level;
  const riskClass = prediction?.risk_category
    ? RISK_COLORS[prediction.risk_category] ?? 'bg-gray-100 text-gray-600'
    : null;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-xl border border-gray-200 p-4 flex flex-wrap gap-4 items-center justify-between">
        <div>
          <h2 className="text-lg font-bold text-gray-800">LSTM Next-Hour Prediction</h2>
          <p className="text-xs text-amber-600 mt-0.5">
            ⚠ Based on HISTORICAL training data — Not live telemetry
          </p>
        </div>
        <div className="flex gap-3 flex-wrap items-center">
          <select
            value={stationId ?? ''}
            onChange={(e) => { setStationId(Number(e.target.value)); setPrediction(null); }}
            className="border border-gray-300 rounded-lg px-3 py-1.5 text-sm"
          >
            {stations.map((s) => (
              <option key={s.id} value={s.id}>{s.name}</option>
            ))}
          </select>
          <button
            onClick={handleRunPrediction}
            disabled={predLoading || stationId == null}
            className="px-4 py-1.5 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 disabled:opacity-50"
          >
            {predLoading ? 'Running…' : '▶ Run LSTM Prediction'}
          </button>
        </div>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-red-700 text-sm">{error}</div>
      )}
      {predError && (
        <div className="bg-orange-50 border border-orange-200 rounded-lg p-3 text-orange-700 text-sm">
          <strong>Prediction error:</strong> {predError}
        </div>
      )}

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white rounded-xl border border-gray-200 p-4">
          <p className="text-xs text-gray-500 mb-1">Current Level</p>
          <p className="text-2xl font-bold text-gray-800">
            {latestLevel != null ? `${latestLevel.toFixed(2)} m` : '—'}
          </p>
          <p className="text-xs text-gray-400 mt-1">Latest observation</p>
        </div>
        <div className="bg-white rounded-xl border border-gray-200 p-4">
          <p className="text-xs text-gray-500 mb-1">Predicted Next Hour</p>
          <p className="text-2xl font-bold text-blue-700">
            {prediction?.predicted_level != null ? `${prediction.predicted_level.toFixed(2)} m` : '—'}
          </p>
          <p className="text-xs text-gray-400 mt-1">LSTM forecast</p>
        </div>
        <div className="bg-white rounded-xl border border-gray-200 p-4">
          <p className="text-xs text-gray-500 mb-1">Trend</p>
          <div className="flex items-center gap-2 mt-1">
            {trendIcon}
            <span className="text-lg font-semibold text-gray-700 capitalize">{trend ?? '—'}</span>
          </div>
          <p className="text-xs text-gray-400 mt-1">Last 2 observations</p>
        </div>
        <div className="bg-white rounded-xl border border-gray-200 p-4">
          <p className="text-xs text-gray-500 mb-1">Flood Risk</p>
          {riskClass ? (
            <span className={`inline-block px-3 py-1 rounded-full text-sm font-semibold ${riskClass}`}>
              {prediction.risk_category}
            </span>
          ) : (
            <span className="text-gray-400 text-sm">Run prediction first</span>
          )}
          <p className="text-xs text-gray-400 mt-1">
            {prediction?.threshold_source === 'VERIFIED_CWC' ? '✅ CWC Verified' : prediction ? '⚠ Unverified' : ''}
          </p>
        </div>
      </div>

      {/* Chart */}
      <div className="bg-white rounded-xl border border-gray-200 p-4">
        <h3 className="font-semibold text-gray-700 mb-3">Last 24 h + Next-Hour Forecast</h3>
        {loading ? (
          <div className="flex justify-center py-16">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
          </div>
        ) : chartData.length === 0 ? (
          <p className="text-gray-400 text-sm py-8 text-center">No observations available.</p>
        ) : (
          <ResponsiveContainer width="100%" height={320}>
            <ComposedChart data={chartData} margin={{ top: 5, right: 30, left: 0, bottom: 20 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="time" tick={{ fontSize: 10 }} angle={-30} textAnchor="end" interval="preserveStartEnd" />
              <YAxis tick={{ fontSize: 11 }} unit=" m" />
              <Tooltip
                contentStyle={{ fontSize: 12 }}
                formatter={(v, name) => [`${v} m`, name === 'predicted' ? '🔮 Predicted' : '📊 Observed']}
              />
              <Legend />
              <Line
                type="monotone"
                dataKey="water_level"
                name="Observed"
                stroke="#2563eb"
                dot={false}
                strokeWidth={2}
                connectNulls={false}
              />
              <Line
                type="monotone"
                dataKey="predicted"
                name="Predicted (LSTM)"
                stroke="#f97316"
                dot={{ r: 6, fill: '#f97316' }}
                strokeWidth={2.5}
                strokeDasharray="8 4"
                connectNulls={false}
              />
            </ComposedChart>
          </ResponsiveContainer>
        )}
      </div>

      {prediction && (
        <div className="bg-white rounded-xl border border-gray-200 p-4 text-sm space-y-2">
          <h3 className="font-semibold text-gray-700">Prediction Details</h3>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3 text-xs text-gray-600">
            <div><span className="font-medium">Confidence:</span> {prediction.confidence != null ? `${(prediction.confidence * 100).toFixed(0)}%` : 'N/A'}</div>
            <div><span className="font-medium">Model:</span> LSTM (24-step input)</div>
            <div><span className="font-medium">Threshold source:</span> {prediction.threshold_source ?? 'N/A'}</div>
            <div><span className="font-medium">Predicted at:</span> {prediction.predicted_at ? new Date(prediction.predicted_at).toLocaleString() : 'N/A'}</div>
            <div><span className="font-medium">Input length:</span> {prediction.input_length ?? 24} observations</div>
            <div><span className="font-medium">Data type:</span> <span className="text-amber-600">HISTORICAL</span></div>
          </div>
          {prediction.notes && (
            <p className="text-xs text-gray-500 italic border-t border-gray-100 pt-2">{prediction.notes}</p>
          )}
        </div>
      )}
    </div>
  );
}
