/**
 * SmartPortPage
 *
 * Main page for SmartPort port management system
 */
import React, { useState } from 'react';
import { useSmartPort } from '../hooks/useSmartPort';
import { PortKPIDashboard } from '../components/smartport/PortKPIDashboard';
import { PortMap } from '../components/smartport/PortMap';
import { BerthStatusGrid } from '../components/smartport/BerthStatusGrid';
import { VesselList } from '../components/smartport/VesselList';
import { OperationProgress } from '../components/smartport/OperationProgress';
import { RealTimePLCViewer } from '../components/smartport/RealTimePLCViewer';
import { HistoricalTrendChart } from '../components/smartport/HistoricalTrendChart';
import { ChatBotWidget } from '../components/smartport/ChatBotWidget';
import { Berth, Vessel, PortOperation } from '../api/smartport';
import { RefreshCw, Activity, Wifi, WifiOff, Gauge } from 'lucide-react';

export const SmartPortPage: React.FC = () => {
  const {
    berths,
    vessels,
    operations,
    kpis,
    loading,
    connected,
    refreshAll,
  } = useSmartPort();

  const [selectedBerthId, setSelectedBerthId] = useState<string | undefined>();
  const [selectedTab, setSelectedTab] = useState<'overview' | 'berths' | 'vessels' | 'operations' | 'plc'>('overview');
  const [selectedPLCTag, setSelectedPLCTag] = useState<string>('crane_1_position');

  const handleBerthClick = (berth: Berth) => {
    setSelectedBerthId(berth.id);
  };

  const handleVesselClick = (vessel: Vessel) => {
    console.log('Vessel clicked:', vessel);
    // Navigate to vessel details or show modal
  };

  const handleOperationClick = (operation: PortOperation) => {
    console.log('Operation clicked:', operation);
    // Navigate to operation details or show modal
  };

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">SmartPort</h1>
              <p className="text-sm text-gray-500">Port Management System</p>
            </div>

            <div className="flex items-center gap-4">
              {/* WebSocket status */}
              <div className="flex items-center gap-2">
                {connected ? (
                  <>
                    <Wifi className="h-5 w-5 text-green-500" />
                    <span className="text-sm text-green-600">Real-time Connected</span>
                  </>
                ) : (
                  <>
                    <WifiOff className="h-5 w-5 text-red-500" />
                    <span className="text-sm text-red-600">Disconnected</span>
                  </>
                )}
              </div>

              {/* Refresh button */}
              <button
                onClick={refreshAll}
                disabled={loading}
                className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
                Refresh
              </button>
            </div>
          </div>

          {/* Tabs */}
          <div className="mt-4 border-b border-gray-200">
            <nav className="-mb-px flex space-x-8">
              <button
                onClick={() => setSelectedTab('overview')}
                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                  selectedTab === 'overview'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <div className="flex items-center gap-2">
                  <Activity className="h-4 w-4" />
                  Overview
                </div>
              </button>
              <button
                onClick={() => setSelectedTab('berths')}
                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                  selectedTab === 'berths'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                Berths ({berths.length})
              </button>
              <button
                onClick={() => setSelectedTab('vessels')}
                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                  selectedTab === 'vessels'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                Vessels ({vessels.length})
              </button>
              <button
                onClick={() => setSelectedTab('operations')}
                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                  selectedTab === 'operations'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                Operations ({operations.length})
              </button>
              <button
                onClick={() => setSelectedTab('plc')}
                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                  selectedTab === 'plc'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <div className="flex items-center gap-2">
                  <Gauge className="h-4 w-4" />
                  PLC Monitor
                </div>
              </button>
            </nav>
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {selectedTab === 'overview' && (
          <div className="space-y-6">
            {/* KPIs */}
            <PortKPIDashboard kpis={kpis} loading={loading} />

            {/* Port Map and Operations */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <PortMap
                berths={berths}
                selectedBerthId={selectedBerthId}
                onBerthClick={handleBerthClick}
              />
              <OperationProgress
                operations={operations.slice(0, 5)}
                onOperationClick={handleOperationClick}
              />
            </div>

            {/* Recent vessels */}
            <VesselList
              vessels={vessels.slice(0, 10)}
              onVesselClick={handleVesselClick}
              title="Recent Vessels"
            />
          </div>
        )}

        {selectedTab === 'berths' && (
          <div className="space-y-6">
            <PortMap
              berths={berths}
              selectedBerthId={selectedBerthId}
              onBerthClick={handleBerthClick}
            />
            <BerthStatusGrid berths={berths} onBerthClick={handleBerthClick} />
          </div>
        )}

        {selectedTab === 'vessels' && (
          <VesselList
            vessels={vessels}
            onVesselClick={handleVesselClick}
            title="All Vessels"
          />
        )}

        {selectedTab === 'operations' && (
          <OperationProgress operations={operations} onOperationClick={handleOperationClick} />
        )}

        {selectedTab === 'plc' && (
          <div className="space-y-6">
            {/* Real-time PLC Viewer */}
            <RealTimePLCViewer showAllTags={true} />

            {/* Historical Trend and ChatBot - Side by Side */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Historical Chart - Takes 2 columns */}
              <div className="lg:col-span-2">
                <HistoricalTrendChart
                  tagName={selectedPLCTag}
                  hours={24}
                  chartType="area"
                  showStatistics={true}
                />

                {/* Tag Selector */}
                <div className="mt-4 bg-white rounded-lg shadow-sm p-4">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Select Tag for Historical View:
                  </label>
                  <select
                    value={selectedPLCTag}
                    onChange={(e) => setSelectedPLCTag(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    <option value="crane_1_position">Crane 1 Position</option>
                    <option value="crane_1_load">Crane 1 Load</option>
                    <option value="crane_1_speed">Crane 1 Speed</option>
                    <option value="berth_t1a_containers">Berth T1-A Containers</option>
                    <option value="port_throughput">Port Throughput</option>
                  </select>
                </div>
              </div>

              {/* ChatBot Widget - Takes 1 column */}
              <div className="lg:col-span-1">
                <ChatBotWidget includeContext={true} className="h-full" />
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
};
