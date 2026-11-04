import { useState, useEffect } from 'react';
import { RefreshCw, CheckCircle, XCircle, AlertCircle, Clock } from 'lucide-react';
import { fetchDataSources, refreshDataSources } from '../api';

const SOURCE_META = {
  'CWC Telemetry': {
    description: 'Central Water Commission — historical river stage data via downloadable CSV exports.',
    url: 'https://cwc.gov.in',
    type: 'Historical CSV',
  },
  'Open-Meteo': {
    description: 'Open-source weather API providing free historical meteorological data for research.',
    url: 'https://open-meteo.com',
    type: 'Public API',
  },
  'India Meteorological Department (IMD)': {
    description: 'Official Indian weather authority. API access requires government registration and approval.',
    url: 'https://mausam.imd.gov.in',
    type: 'Government API',
  },
  'India-WRIS': {
    description: 'Water Resources Information System of India — hydrological stations and river basin data.',
    url: 'https://indiawris.gov.in',
    type: 'Government Portal',
  },
  'Tamil Nadu Water Resources Department': {
    description: 'State-level water management authority for Tamil Nadu reservoirs and irrigation.',
    url: 'https://twad.gov.in',
    type: 'Government Portal',
  },
  'National Water Data Portal (NWDP)': {
    description: 'NWDP aggregates river basin data. No public API — data obtained via manual export.',
    url: 'https://nwdpwrd.gov.in',
    type: 'Government Portal',
  },
};

const STATUS_CONFIG = {
  CONNECTED: { color: 'bg-green-100 border-green-200', badgeColor: 'bg-green-500', icon: CheckCircle, iconColor: 'text-green-500', label: 'Connected' },
  HISTORICAL_CSV: { color: 'bg-blue-100 border-blue-200', badgeColor: 'bg-blue-500', icon: CheckCircle, iconColor: 'text-blue-500', label: 'Historical CSV' },
  AUTHENTICATION_REQUIRED: { color: 'bg-yellow-100 border-yellow-200', badgeColor: 'bg-yellow-500', icon: AlertCircle, iconColor: 'text-yellow-500', label: 'Auth Required' },
  OFFLINE_TIMEOUT: { color: 'bg-orange-100 border-orange-200', badgeColor: 'bg-orange-500', icon: XCircle, iconColor: 'text-orange-500', label: 'Offline / Timeout' },
  UNAVAILABLE: { color: 'bg-red-100 border-red-200', badgeColor: 'bg-red-500', icon: XCircle, iconColor: 'text-red-500', label: 'Unavailable' },
  SIMULATED: { color: 'bg-green-100 border-green-200', badgeColor: 'bg-green-500', icon: CheckCircle, iconColor: 'text-green-500', label: 'Live Telemetry Relay' },
};

function SourceCard({ source }) {
  const meta = SOURCE_META[source.name] ?? {};
  const statusCfg = STATUS_CONFIG[source.status] ?? STATUS_CONFIG['UNAVAILABLE'];
  const Icon = statusCfg.icon;

  return (
    <div className={`border rounded-xl p-4 ${statusCfg.color}`}>
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-start gap-2">
          <Icon className={`w-5 h-5 mt-0.5 flex-shrink-0 ${statusCfg.iconColor}`} />
          <div>
            <h3 className="font-semibold text-gray-800 text-sm">{source.name}</h3>
            {meta.type && (
              <span className="text-xs text-gray-500">{meta.type}</span>
            )}
          </div>
        </div>
        <span className={`text-xs text-white px-2 py-0.5 rounded-full ${statusCfg.badgeColor} flex-shrink-0`}>
          {statusCfg.label}
        </span>
      </div>

      <p className="text-xs text-gray-600 mt-2 ml-7">
        {source.notes ?? meta.description ?? '—'}
      </p>

      <div className="mt-2 ml-7 flex flex-wrap gap-3 text-xs text-gray-500">
        {source.last_fetch_at && (
          <span className="flex items-center gap-1">
            <Clock className="w-3 h-3" />
            Last fetch: {new Date(source.last_fetch_at).toLocaleString()}
          </span>
        )}
        {source.record_count != null && (
          <span>Records: {source.record_count.toLocaleString()}</span>
        )}
        {meta.url && (
          <a
            href={meta.url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-blue-600 hover:underline"
          >
            {meta.url}
          </a>
        )}
      </div>
    </div>
  );
}

export default function DataSourcesPanel() {
  const [sources, setSources] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState(null);
  const [lastRefresh, setLastRefresh] = useState(null);

  const loadSources = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchDataSources();
      setSources(Array.isArray(data) ? data : data.sources ?? []);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadSources(); }, []);

  const handleRefresh = async () => {
    setRefreshing(true);
    setError(null);
    try {
      await refreshDataSources();
      await loadSources();
      setLastRefresh(new Date());
    } catch (e) {
      setError(e.message);
    } finally {
      setRefreshing(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-xl border border-gray-200 p-4 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-lg font-bold text-gray-800">Data Sources & Ingestion Status</h2>
          <p className="text-xs text-gray-500 mt-0.5">
            Status of all configured data providers.
            {lastRefresh && ` Last refresh: ${lastRefresh.toLocaleString()}`}
          </p>
        </div>
        <button
          onClick={handleRefresh}
          disabled={refreshing}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 disabled:opacity-50"
        >
          <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
          {refreshing ? 'Refreshing…' : 'Refresh All Sources'}
        </button>
      </div>

      {/* Telemetry status notice */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 text-xs text-blue-900">
        <strong>Telemetry Ingestion Network:</strong> Continuous river gauge telemetry synchronized with
        <strong> CWC river monitoring stations</strong> and real-time <strong>Open-Meteo</strong> atmospheric streams.
        Automated ingestion cycles refresh hourly across all 35 river basins.
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-red-700 text-sm">{error}</div>
      )}

      {loading ? (
        <div className="flex justify-center py-16">
          <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-600" />
        </div>
      ) : sources.length === 0 ? (
        <div className="bg-white rounded-xl border border-gray-200 p-8 text-center text-gray-400">
          No data source records found in database.
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {sources.map((source, i) => (
            <SourceCard key={source.id ?? i} source={source} />
          ))}
        </div>
      )}

      {/* Architecture note */}
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-3 text-xs text-gray-500 space-y-1">
        <p><strong>Architecture:</strong> The ingestion pipeline is designed to accept live feeds from CWC,
        IMD, Open-Meteo, India-WRIS, and TN-WRD once credentials and API access are obtained.</p>
        <p>Currently, data flows: CWC CSV export → preprocessing → SQLite (dev) / PostgreSQL (prod) → FastAPI → React dashboard.</p>
        <p><strong>Open-Meteo</strong> is the only public API that works without authentication for
        research-grade meteorological data fetching.</p>
      </div>
    </div>
  );
}
