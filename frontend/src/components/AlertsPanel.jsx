import { useState, useEffect } from 'react';
import { Bell, BellOff, CheckCircle, Clock } from 'lucide-react';
import { fetchAlerts, fetchAllAlerts, acknowledgeAlert } from '../api';

const SEVERITY_STYLES = {
  Extreme: 'bg-red-100 text-red-700 border-red-200',
  Severe: 'bg-orange-100 text-orange-700 border-orange-200',
  'Above Normal': 'bg-yellow-100 text-yellow-700 border-yellow-200',
  Normal: 'bg-green-100 text-green-700 border-green-200',
};

const SEVERITY_DOT = {
  Extreme: 'bg-red-500',
  Severe: 'bg-orange-500',
  'Above Normal': 'bg-yellow-500',
  Normal: 'bg-green-500',
};

function AlertCard({ alert, onAcknowledge }) {
  const style = SEVERITY_STYLES[alert.severity] ?? 'bg-gray-100 text-gray-700 border-gray-200';
  const dot = SEVERITY_DOT[alert.severity] ?? 'bg-gray-400';

  return (
    <div className={`border rounded-xl p-4 ${style}`}>
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-start gap-3">
          <span className={`w-3 h-3 rounded-full flex-shrink-0 mt-1 ${dot}`} />
          <div>
            <div className="flex items-center gap-2 flex-wrap">
              <span className="font-semibold text-sm">{alert.station_name ?? `Station ${alert.station_id}`}</span>
              <span className={`text-xs px-2 py-0.5 rounded-full border ${style}`}>{alert.severity}</span>
              {alert.is_acknowledged && (
                <span className="text-xs text-gray-500 flex items-center gap-1">
                  <CheckCircle className="w-3 h-3" /> Acknowledged
                </span>
              )}
            </div>
            <p className="text-xs mt-1 opacity-80">{alert.message ?? 'Flood risk alert'}</p>
            <p className="text-xs mt-1 opacity-60 flex items-center gap-1">
              <Clock className="w-3 h-3" />
              {alert.created_at ? new Date(alert.created_at).toLocaleString() : '—'}
              {alert.acknowledged_by && ` · Acknowledged by ${alert.acknowledged_by}`}
            </p>
          </div>
        </div>
        {!alert.is_acknowledged && onAcknowledge && (
          <button
            onClick={() => onAcknowledge(alert.id)}
            className="flex-shrink-0 px-3 py-1.5 bg-white bg-opacity-70 hover:bg-opacity-100 border border-current rounded-lg text-xs font-medium transition"
          >
            Acknowledge
          </button>
        )}
      </div>
    </div>
  );
}

export default function AlertsPanel() {
  const [tab, setTab] = useState('active');
  const [activeAlerts, setActiveAlerts] = useState([]);
  const [allAlerts, setAllAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [ackLoading, setAckLoading] = useState(null);

  const loadAlerts = async () => {
    setLoading(true);
    setError(null);
    try {
      const [active, all] = await Promise.all([fetchAlerts(), fetchAllAlerts()]);
      setActiveAlerts(active);
      setAllAlerts(all);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadAlerts(); }, []);

  const handleAcknowledge = async (alertId) => {
    setAckLoading(alertId);
    try {
      await acknowledgeAlert(alertId);
      await loadAlerts();
    } catch (e) {
      setError(e.message);
    } finally {
      setAckLoading(null);
    }
  };

  const displayList = tab === 'active' ? activeAlerts : allAlerts;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-xl border border-gray-200 p-4 flex items-center justify-between flex-wrap gap-3">
        <div>
          <h2 className="text-lg font-bold text-gray-800">Flood Alerts</h2>
          <p className="text-xs text-gray-500 mt-0.5">
            {activeAlerts.filter((a) => !a.is_acknowledged).length} unacknowledged active alerts
          </p>
        </div>
        <button
          onClick={loadAlerts}
          className="px-3 py-1.5 bg-gray-100 hover:bg-gray-200 rounded-lg text-sm text-gray-700"
        >
          🔄 Refresh
        </button>
      </div>

      {/* Tabs */}
      <div className="flex gap-2">
        {[
          { key: 'active', label: `Active (${activeAlerts.length})`, Icon: Bell },
          { key: 'all', label: `All History (${allAlerts.length})`, Icon: BellOff },
        ].map(({ key, label, Icon }) => (
          <button
            key={key}
            onClick={() => setTab(key)}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition ${
              tab === key
                ? 'bg-blue-600 text-white'
                : 'bg-white border border-gray-200 text-gray-600 hover:bg-gray-50'
            }`}
          >
            <Icon className="w-4 h-4" />
            {label}
          </button>
        ))}
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-red-700 text-sm">{error}</div>
      )}

      {loading ? (
        <div className="flex justify-center py-16">
          <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-600" />
        </div>
      ) : displayList.length === 0 ? (
        <div className="bg-white rounded-xl border border-gray-200 p-12 text-center">
          <CheckCircle className="w-10 h-10 text-green-400 mx-auto mb-3" />
          <p className="text-gray-500">No alerts in this category.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {displayList.map((alert) => (
            <AlertCard
              key={alert.id}
              alert={alert}
              onAcknowledge={tab === 'active' ? handleAcknowledge : null}
            />
          ))}
        </div>
      )}

      {ackLoading && (
        <div className="text-center text-xs text-gray-400">Acknowledging alert {ackLoading}…</div>
      )}
    </div>
  );
}
