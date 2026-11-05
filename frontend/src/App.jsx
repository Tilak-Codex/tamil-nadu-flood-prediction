import { useState, useEffect, useCallback } from 'react';
import Navbar from './components/Navbar';
import Overview from './components/Overview';
import StationMap from './components/StationMap';
import FloodRiskStatus from './components/FloodRiskStatus';
import AlertsPanel from './components/AlertsPanel';
import { fetchStations, fetchAlerts, fetchDashboardStats, fetchMapSummary } from './api';

export default function App() {
  const [activeTab, setActiveTab] = useState('overview');
  const [selectedStationId, setSelectedStationId] = useState(null);
  const [stations, setStations] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [stats, setStats] = useState(null);
  const [mapSummary, setMapSummary] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadInitialData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [stationsData, alertsData, statsData, mapSummaryData] = await Promise.allSettled([
        fetchStations(),
        fetchAlerts(),
        fetchDashboardStats(),
        fetchMapSummary(),
      ]);
      if (stationsData.status === 'fulfilled') setStations(stationsData.value);
      if (alertsData.status === 'fulfilled') setAlerts(alertsData.value);
      if (statsData.status === 'fulfilled') setStats(statsData.value);
      if (mapSummaryData.status === 'fulfilled') setMapSummary(mapSummaryData.value);
    } catch {
      setError('Failed to connect to backend. Is the FastAPI server running on port 8000?');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadInitialData();
    // Auto-refresh every 5 minutes
    const interval = setInterval(loadInitialData, 300_000);
    return () => clearInterval(interval);
  }, [loadInitialData]);

  const handleSelectStation = (stationId) => {
    setSelectedStationId(stationId);
    setActiveTab('map');
  };

  const handleNavigateTab = (tab) => setActiveTab(tab);

  const activeAlertCount = alerts.filter((a) => !a.is_acknowledged).length;

  const renderContent = () => {
    if (loading) {
      return (
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4" />
            <p className="text-gray-500">Connecting to backend…</p>
          </div>
        </div>
      );
    }

    if (error) {
      return (
        <div className="p-6">
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <h3 className="font-semibold text-red-800 mb-1">Backend Unreachable</h3>
            <p className="text-red-600 text-sm">{error}</p>
            <p className="text-red-500 text-xs mt-2">
              Run: <code className="bg-red-100 px-1 rounded">uvicorn src.api.app:app --host 0.0.0.0 --port 8000 --reload</code>
            </p>
            <button
              onClick={loadInitialData}
              className="mt-3 px-4 py-2 bg-red-600 text-white text-sm rounded hover:bg-red-700"
            >
              Retry
            </button>
          </div>
        </div>
      );
    }

    switch (activeTab) {
      case 'overview':
        return (
          <Overview
            stations={stations}
            alerts={alerts}
            stats={stats}
            onSelectStation={handleSelectStation}
            onNavigateTab={handleNavigateTab}
          />
        );
      case 'map':
        return (
          <StationMap
            stations={stations}
            mapSummary={mapSummary}
            onSelectStation={handleSelectStation}
          />
        );
      case 'risk':
        return <FloodRiskStatus stations={stations} onSelectStation={handleSelectStation} />;
      case 'alerts':
        return <AlertsPanel />;
      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar
        activeTab={activeTab}
        onTabChange={handleNavigateTab}
        alertCount={activeAlertCount}
      />
      <main className="max-w-screen-xl mx-auto px-4 py-6">
        {renderContent()}
      </main>
      <footer className="text-center text-xs text-gray-400 py-4 border-t border-gray-200 mt-8">
        AI-Based Flood Prediction &amp; Decision Support System — Tamil Nadu &nbsp;|&nbsp;
        Data: CWC Historical Records &nbsp;|&nbsp;
        <span className="text-amber-500">All data is HISTORICAL / SIMULATED — Not live telemetry</span>
      </footer>
    </div>
  );
}
