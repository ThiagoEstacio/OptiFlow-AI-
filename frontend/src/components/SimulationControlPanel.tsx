/**
 * Simulation Control Panel
 *
 * Panel for controlling the tag data simulator and testing alarm conditions
 */

import React, { useState, useEffect } from 'react';
import {
  Play,
  Pause,
  AlertTriangle,
  Ship,
  Truck,
  Zap,
  ThermometerSun,
  Wind,
  RefreshCw,
  X
} from 'lucide-react';
import { tagDataSimulator, AlarmCondition } from '../services/tagDataSimulator';

interface SimulationControlPanelProps {
  onClose?: () => void;
}

export const SimulationControlPanel: React.FC<SimulationControlPanelProps> = ({ onClose }) => {
  const [isSimulating, setIsSimulating] = useState(false);
  const [shipLoadingActive, setShipLoadingActive] = useState(false);
  const [truckReceivingActive, setTruckReceivingActive] = useState(true);
  const [alarmsEnabled, setAlarmsEnabled] = useState(true);
  const [alarms, setAlarms] = useState<AlarmCondition[]>([]);
  const [simulationSpeed, setSimulationSpeed] = useState(1.0);

  useEffect(() => {
    let intervalId: NodeJS.Timeout | null = null;

    if (isSimulating) {
      intervalId = setInterval(() => {
        tagDataSimulator.updateValues();
        setAlarms(tagDataSimulator.getActiveAlarms());
      }, 5000 / simulationSpeed); // Update every 5 seconds adjusted by speed
    }

    return () => {
      if (intervalId) clearInterval(intervalId);
    };
  }, [isSimulating, simulationSpeed]);

  const handleShipLoadingToggle = () => {
    const newState = !shipLoadingActive;
    setShipLoadingActive(newState);
    tagDataSimulator.setShipLoadingActive(newState);
  };

  const handleTruckReceivingToggle = () => {
    const newState = !truckReceivingActive;
    setTruckReceivingActive(newState);
    tagDataSimulator.setTruckReceivingActive(newState);
  };

  const handleAlarmsToggle = () => {
    const newState = !alarmsEnabled;
    setAlarmsEnabled(newState);
    tagDataSimulator.setAlarmsEnabled(newState);
  };

  const handleSpeedChange = (speed: number) => {
    setSimulationSpeed(speed);
    tagDataSimulator.setSimulationSpeed(speed);
  };

  const handleReset = () => {
    tagDataSimulator.reset();
    setAlarms([]);
    setShipLoadingActive(false);
    setTruckReceivingActive(true);
    tagDataSimulator.setShipLoadingActive(false);
    tagDataSimulator.setTruckReceivingActive(true);
  };

  const triggerTestAlarm = (type: 'temp' | 'pressure' | 'vibration') => {
    switch (type) {
      case 'temp':
        tagDataSimulator.triggerHighTemperatureAlarm();
        break;
      case 'pressure':
        console.log('⚠️ Pressure alarm simulation - use gate controls to affect pressure');
        break;
      case 'vibration':
        tagDataSimulator.triggerConveyorJam();
        break;
    }
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6 border border-gray-200 dark:border-gray-700">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-blue-100 dark:bg-blue-900 rounded-lg">
            <Zap className="w-6 h-6 text-blue-600 dark:text-blue-300" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-gray-900 dark:text-white">
              Simulation Control Panel
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Control port terminal operations and test scenarios
            </p>
          </div>
        </div>
        {onClose && (
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
          >
            <X className="w-5 h-5 text-gray-500 dark:text-gray-400" />
          </button>
        )}
      </div>

      {/* Main Controls */}
      <div className="space-y-4 mb-6">
        {/* Simulation Control */}
        <div className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
          <div>
            <div className="font-semibold text-gray-900 dark:text-white">Simulation Status</div>
            <div className="text-sm text-gray-600 dark:text-gray-400">
              {isSimulating ? 'Running' : 'Paused'}
            </div>
          </div>
          <button
            onClick={() => setIsSimulating(!isSimulating)}
            className={`flex items-center space-x-2 px-4 py-2 rounded-lg font-medium transition-colors ${
              isSimulating
                ? 'bg-orange-500 hover:bg-orange-600 text-white'
                : 'bg-green-500 hover:bg-green-600 text-white'
            }`}
          >
            {isSimulating ? (
              <>
                <Pause className="w-4 h-4" />
                <span>Pause</span>
              </>
            ) : (
              <>
                <Play className="w-4 h-4" />
                <span>Start</span>
              </>
            )}
          </button>
        </div>

        {/* Simulation Speed */}
        <div className="p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
          <div className="flex items-center justify-between mb-2">
            <div className="font-semibold text-gray-900 dark:text-white">Simulation Speed</div>
            <span className="text-sm font-mono text-gray-600 dark:text-gray-400">{simulationSpeed.toFixed(1)}x</span>
          </div>
          <input
            type="range"
            min="0.5"
            max="5"
            step="0.5"
            value={simulationSpeed}
            onChange={(e) => handleSpeedChange(parseFloat(e.target.value))}
            className="w-full"
          />
          <div className="flex justify-between text-xs text-gray-500 dark:text-gray-400 mt-1">
            <span>0.5x</span>
            <span>1x</span>
            <span>5x</span>
          </div>
        </div>
      </div>

      {/* Process Controls */}
      <div className="space-y-3 mb-6">
        <h4 className="font-semibold text-gray-900 dark:text-white mb-2">Process Controls</h4>

        {/* Ship Loading */}
        <div className="flex items-center justify-between p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
          <div className="flex items-center space-x-3">
            <Ship className="w-5 h-5 text-blue-600 dark:text-blue-400" />
            <div>
              <div className="font-medium text-gray-900 dark:text-white">Ship Loading</div>
              <div className="text-xs text-gray-600 dark:text-gray-400">
                Shiploader operation
              </div>
            </div>
          </div>
          <button
            onClick={handleShipLoadingToggle}
            className={`px-4 py-2 rounded-lg font-medium text-sm transition-colors ${
              shipLoadingActive
                ? 'bg-blue-600 hover:bg-blue-700 text-white'
                : 'bg-gray-300 dark:bg-gray-600 hover:bg-gray-400 dark:hover:bg-gray-500 text-gray-700 dark:text-gray-300'
            }`}
          >
            {shipLoadingActive ? 'Active' : 'Inactive'}
          </button>
        </div>

        {/* Truck Receiving */}
        <div className="flex items-center justify-between p-3 bg-green-50 dark:bg-green-900/20 rounded-lg border border-green-200 dark:border-green-800">
          <div className="flex items-center space-x-3">
            <Truck className="w-5 h-5 text-green-600 dark:text-green-400" />
            <div>
              <div className="font-medium text-gray-900 dark:text-white">Truck Reception</div>
              <div className="text-xs text-gray-600 dark:text-gray-400">
                Grain receiving
              </div>
            </div>
          </div>
          <button
            onClick={handleTruckReceivingToggle}
            className={`px-4 py-2 rounded-lg font-medium text-sm transition-colors ${
              truckReceivingActive
                ? 'bg-green-600 hover:bg-green-700 text-white'
                : 'bg-gray-300 dark:bg-gray-600 hover:bg-gray-400 dark:hover:bg-gray-500 text-gray-700 dark:text-gray-300'
            }`}
          >
            {truckReceivingActive ? 'Active' : 'Inactive'}
          </button>
        </div>
      </div>

      {/* Alarm Controls */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-3">
          <h4 className="font-semibold text-gray-900 dark:text-white">Alarms</h4>
          <button
            onClick={handleAlarmsToggle}
            className={`px-3 py-1 rounded-lg text-sm font-medium transition-colors ${
              alarmsEnabled
                ? 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300'
                : 'bg-gray-200 dark:bg-gray-700 text-gray-600 dark:text-gray-400'
            }`}
          >
            {alarmsEnabled ? 'Enabled' : 'Disabled'}
          </button>
        </div>

        {/* Active Alarms */}
        {alarmsEnabled && alarms.length > 0 && (
          <div className="space-y-2 mb-3">
            {alarms.slice(0, 3).map((alarm, index) => (
              <div
                key={index}
                className="flex items-start space-x-2 p-2 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg"
              >
                <AlertTriangle className="w-4 h-4 text-red-600 dark:text-red-400 mt-0.5 flex-shrink-0" />
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-medium text-red-900 dark:text-red-200 truncate">
                    {alarm.tagName}
                  </div>
                  <div className="text-xs text-red-700 dark:text-red-300">
                    {alarm.condition === 'high' ? 'High' : 'Low'} - {alarm.value.toFixed(2)} (Limit: {alarm.threshold})
                  </div>
                </div>
              </div>
            ))}
            {alarms.length > 3 && (
              <div className="text-xs text-gray-500 dark:text-gray-400 text-center">
                +{alarms.length - 3} more alarms
              </div>
            )}
          </div>
        )}

        {/* Test Alarm Buttons */}
        <div className="grid grid-cols-3 gap-2">
          <button
            onClick={() => triggerTestAlarm('temp')}
            className="p-2 bg-orange-100 dark:bg-orange-900/30 hover:bg-orange-200 dark:hover:bg-orange-900/50 text-orange-700 dark:text-orange-300 rounded-lg text-xs font-medium transition-colors flex items-center justify-center space-x-1"
          >
            <ThermometerSun className="w-3 h-3" />
            <span>High Temp</span>
          </button>
          <button
            onClick={() => triggerTestAlarm('pressure')}
            className="p-2 bg-blue-100 dark:bg-blue-900/30 hover:bg-blue-200 dark:hover:bg-blue-900/50 text-blue-700 dark:text-blue-300 rounded-lg text-xs font-medium transition-colors flex items-center justify-center space-x-1"
          >
            <Wind className="w-3 h-3" />
            <span>Low Pressure</span>
          </button>
          <button
            onClick={() => triggerTestAlarm('vibration')}
            className="p-2 bg-purple-100 dark:bg-purple-900/30 hover:bg-purple-200 dark:hover:bg-purple-900/50 text-purple-700 dark:text-purple-300 rounded-lg text-xs font-medium transition-colors flex items-center justify-center space-x-1"
          >
            <AlertTriangle className="w-3 h-3" />
            <span>High Vib</span>
          </button>
        </div>
      </div>

      {/* Reset Button */}
      <button
        onClick={handleReset}
        className="w-full flex items-center justify-center space-x-2 px-4 py-2 bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 rounded-lg font-medium transition-colors"
      >
        <RefreshCw className="w-4 h-4" />
        <span>Reset Simulation</span>
      </button>

      {/* Info */}
      <div className="mt-4 p-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
        <div className="text-xs text-blue-700 dark:text-blue-300">
          <strong>💡 Tip:</strong> Enable simulation to see real-time data updates in your widgets.
          Adjust speed to test different scenarios faster.
        </div>
      </div>
    </div>
  );
};

export default SimulationControlPanel;
