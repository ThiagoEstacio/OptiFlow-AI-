/**
 * Devices Management Page
 */
import React, { useEffect } from 'react';
import { useAppDispatch, useAppSelector } from '../store';
import { fetchDevices } from '../store/slices/devicesSlice';

export const DevicesPage: React.FC = () => {
  const dispatch = useAppDispatch();
  const { items: devices, loading } = useAppSelector((state) => state.devices);

  useEffect(() => {
    dispatch(fetchDevices());
  }, [dispatch]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Devices</h1>
          <p className="text-gray-600 mt-1">Manage industrial devices and PLCs</p>
        </div>
        <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
          Add Device
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {devices.length === 0 ? (
          <div className="col-span-full text-center py-12 bg-white rounded-lg shadow">
            <p className="text-gray-500">No devices found. Click "Add Device" to create one.</p>
          </div>
        ) : (
          devices.map((device) => (
            <div key={device.id} className="bg-white rounded-lg shadow p-6 hover:shadow-lg transition-shadow">
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                  <h3 className="text-lg font-semibold text-gray-900">{device.name}</h3>
                  <p className="text-sm text-gray-500 mt-1">{device.description}</p>
                </div>
                <span className={`w-3 h-3 rounded-full flex-shrink-0 ${
                  device.status === 'connected' ? 'bg-green-500' : 'bg-gray-300'
                }`}></span>
              </div>

              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Protocol:</span>
                  <span className="font-medium text-gray-900">{device.protocol.toUpperCase()}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">IP Address:</span>
                  <span className="font-medium text-gray-900">{device.ip_address || 'N/A'}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Port:</span>
                  <span className="font-medium text-gray-900">{device.port || 'N/A'}</span>
                </div>
                {device.last_seen && (
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Last Seen:</span>
                    <span className="font-medium text-gray-900">
                      {new Date(device.last_seen).toLocaleTimeString()}
                    </span>
                  </div>
                )}
              </div>

              <div className="mt-4 pt-4 border-t border-gray-200 flex justify-between">
                <button className="text-blue-600 hover:text-blue-800 text-sm font-medium">
                  View Details
                </button>
                <button className="text-gray-600 hover:text-gray-800 text-sm font-medium">
                  Configure
                </button>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};
