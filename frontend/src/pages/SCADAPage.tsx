import React from 'react';
import { SCADADashboard } from '../components/SCADADashboard';

const SCADAPage: React.FC = () => {
  return (
    <div className="container mx-auto p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900">SCADA Real-Time Monitor</h1>
        <p className="text-gray-600 mt-2">
          Live monitoring of grain terminal simulator - all equipment and process variables
        </p>
      </div>

      <SCADADashboard pollInterval={1000} />

      {/* Info Card */}
      <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h3 className="font-semibold text-blue-900 mb-2">About This Dashboard</h3>
        <p className="text-sm text-blue-800">
          This SCADA (Supervisory Control and Data Acquisition) dashboard provides real-time monitoring
          of the grain terminal simulator. All values are updated every second via the event-driven
          architecture: <strong>Simulator → Kafka → InfluxDB → API → Frontend</strong>.
        </p>
        <ul className="mt-2 text-sm text-blue-800 list-disc list-inside">
          <li><strong>Warehouse Level:</strong> Current inventory percentage</li>
          <li><strong>Total Flow:</strong> Combined flow rate from all gates (t/h)</li>
          <li><strong>Mass Loaded:</strong> Total tonnes processed in current session</li>
          <li><strong>Energy Used:</strong> Total kWh consumed by all equipment</li>
          <li><strong>Gate Status:</strong> Individual gate position and flow rate</li>
        </ul>
      </div>
    </div>
  );
};

export default SCADAPage;
