import React, { useState } from 'react';
import { Wifi, WifiOff, AlertCircle, Tag, Trash2, MoreVertical, Activity } from 'lucide-react';
import { useMutation } from '@tanstack/react-query';
import { devicesApi } from '../api/devices';
import { Device, DeviceStatus } from '../types/device';

interface DeviceCardProps {
  device: Device;
  onUpdate: () => void;
}

export default function DeviceCard({ device, onUpdate }: DeviceCardProps) {
  const [showMenu, setShowMenu] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

  const deleteMutation = useMutation({
    mutationFn: () => devicesApi.delete(device.id),
    onSuccess: () => {
      onUpdate();
    },
  });

  const getStatusIcon = () => {
    switch (device.status) {
      case DeviceStatus.CONNECTED:
        return <Wifi className="h-5 w-5 text-green-600" />;
      case DeviceStatus.DISCONNECTED:
        return <WifiOff className="h-5 w-5 text-gray-400" />;
      case DeviceStatus.ERROR:
        return <AlertCircle className="h-5 w-5 text-red-600" />;
      default:
        return <WifiOff className="h-5 w-5 text-gray-400" />;
    }
  };

  const getStatusText = () => {
    switch (device.status) {
      case DeviceStatus.CONNECTED:
        return 'Connected';
      case DeviceStatus.DISCONNECTED:
        return 'Disconnected';
      case DeviceStatus.ERROR:
        return 'Error';
      default:
        return 'Unknown';
    }
  };

  const getStatusColor = () => {
    switch (device.status) {
      case DeviceStatus.CONNECTED:
        return 'bg-green-100 text-green-800 border-green-200';
      case DeviceStatus.DISCONNECTED:
        return 'bg-gray-100 text-gray-800 border-gray-200';
      case DeviceStatus.ERROR:
        return 'bg-red-100 text-red-800 border-red-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getProtocolBadgeColor = () => {
    switch (device.protocol) {
      case 'opcua':
        return 'bg-blue-100 text-blue-800';
      case 'modbus_tcp':
        return 'bg-purple-100 text-purple-800';
      case 'mqtt':
        return 'bg-orange-100 text-orange-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const handleDelete = () => {
    if (showDeleteConfirm) {
      deleteMutation.mutate();
    } else {
      setShowDeleteConfirm(true);
      setTimeout(() => setShowDeleteConfirm(false), 3000);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-md border border-gray-200 hover:shadow-lg transition-shadow">
      {/* Card Header */}
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center gap-2">
              {getStatusIcon()}
              <h3 className="text-lg font-semibold text-gray-900 truncate">
                {device.name}
              </h3>
            </div>
            {device.description && (
              <p className="text-sm text-gray-500 mt-1 line-clamp-2">{device.description}</p>
            )}
          </div>

          {/* Menu */}
          <div className="relative ml-2">
            <button
              onClick={() => setShowMenu(!showMenu)}
              className="p-1 rounded hover:bg-gray-100 transition-colors"
            >
              <MoreVertical className="h-5 w-5 text-gray-400" />
            </button>

            {showMenu && (
              <>
                <div
                  className="fixed inset-0 z-10"
                  onClick={() => setShowMenu(false)}
                />
                <div className="absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg border border-gray-200 z-20">
                  <button
                    onClick={handleDelete}
                    className="w-full px-4 py-2 text-left text-sm text-red-600 hover:bg-red-50 rounded-md flex items-center"
                  >
                    <Trash2 className="h-4 w-4 mr-2" />
                    {showDeleteConfirm ? 'Click again to confirm' : 'Delete Device'}
                  </button>
                </div>
              </>
            )}
          </div>
        </div>

        {/* Status Badge */}
        <div className="mt-3 flex items-center gap-2">
          <span
            className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${getStatusColor()}`}
          >
            {getStatusText()}
          </span>
          <span
            className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getProtocolBadgeColor()}`}
          >
            {device.protocol.toUpperCase()}
          </span>
        </div>
      </div>

      {/* Card Body */}
      <div className="p-4 space-y-3">
        {/* Connection Info */}
        {device.connection_config?.endpoint && (
          <div className="text-sm">
            <span className="text-gray-500">Endpoint:</span>
            <p className="text-gray-900 font-mono text-xs mt-0.5 truncate">
              {device.connection_config.endpoint}
            </p>
          </div>
        )}

        {/* Metadata */}
        {(device.manufacturer || device.model) && (
          <div className="text-sm">
            <span className="text-gray-500">Device Info:</span>
            <p className="text-gray-900 text-xs mt-0.5">
              {device.manufacturer && <span>{device.manufacturer}</span>}
              {device.manufacturer && device.model && <span> • </span>}
              {device.model && <span>{device.model}</span>}
            </p>
          </div>
        )}

        {/* Stats */}
        <div className="flex items-center justify-between pt-3 border-t border-gray-100">
          <div className="flex items-center text-sm">
            <Tag className="h-4 w-4 text-gray-400 mr-1.5" />
            <span className="text-gray-600">
              <span className="font-semibold text-gray-900">{device.total_tags}</span> tags
            </span>
          </div>
          <div className="flex items-center text-sm">
            <Activity className="h-4 w-4 text-gray-400 mr-1.5" />
            <span className="text-gray-600">
              <span className="font-semibold text-gray-900">
                {device.data_points_collected.toLocaleString()}
              </span>{' '}
              points
            </span>
          </div>
        </div>

        {/* Last Seen */}
        {device.last_seen && (
          <div className="text-xs text-gray-500 pt-2 border-t border-gray-100">
            Last seen: {new Date(device.last_seen).toLocaleString()}
          </div>
        )}

        {/* Error Message */}
        {device.error_message && (
          <div className="mt-2 p-2 bg-red-50 border border-red-200 rounded text-xs text-red-800">
            {device.error_message}
          </div>
        )}
      </div>

      {/* Card Footer */}
      <div className="px-4 py-3 bg-gray-50 border-t border-gray-200 rounded-b-lg">
        <button
          onClick={() => {
            // Navigate to device tags view
            window.location.href = `/tags?device_id=${device.id}`;
          }}
          className="w-full text-sm font-medium text-blue-600 hover:text-blue-700 transition-colors"
        >
          View Tags →
        </button>
      </div>
    </div>
  );
}
