import React, { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { Device, ProtocolType } from '../../types';

interface DeviceFormData {
  name: string;
  device_type: string;
  protocol: ProtocolType;
  site_id: string;
  ip_address: string;
  port: number;
  config?: {
    unit_id?: number;
    node_id?: string;
    endpoint_url?: string;
    rack?: number;
    slot?: number;
    [key: string]: any;
  };
  scan_rate?: number;
  timeout?: number;
  enabled: boolean;
  description?: string;
}

interface DeviceFormProps {
  device?: Device;
  siteId?: string;
  onSubmit: (data: DeviceFormData) => Promise<void>;
  onCancel: () => void;
  isLoading?: boolean;
}

export const DeviceForm: React.FC<DeviceFormProps> = ({
  device,
  siteId,
  onSubmit,
  onCancel,
  isLoading = false,
}) => {
  const {
    register,
    handleSubmit,
    watch,
    formState: { errors },
    reset,
  } = useForm<DeviceFormData>({
    defaultValues: device
      ? {
          name: device.name,
          device_type: device.device_type,
          protocol: device.protocol,
          site_id: device.site_id,
          ip_address: device.ip_address,
          port: device.port,
          config: device.config,
          scan_rate: device.scan_rate,
          timeout: device.timeout,
          enabled: device.enabled,
          description: device.description,
        }
      : {
          site_id: siteId || '',
          enabled: true,
          protocol: 'opcua',
          port: 4840,
          scan_rate: 1000,
          timeout: 5000,
          config: {},
        },
  });

  const selectedProtocol = watch('protocol');

  useEffect(() => {
    if (device) {
      reset({
        name: device.name,
        device_type: device.device_type,
        protocol: device.protocol,
        site_id: device.site_id,
        ip_address: device.ip_address,
        port: device.port,
        config: device.config,
        scan_rate: device.scan_rate,
        timeout: device.timeout,
        enabled: device.enabled,
        description: device.description,
      });
    }
  }, [device, reset]);

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      {/* Basic Information */}
      <div className="space-y-4">
        <h3 className="text-sm font-semibold text-gray-700 uppercase">Basic Information</h3>

        <div>
          <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-1">
            Device Name *
          </label>
          <input
            id="name"
            type="text"
            {...register('name', { required: 'Device name is required' })}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          {errors.name && <p className="mt-1 text-sm text-red-600">{errors.name.message}</p>}
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label htmlFor="device_type" className="block text-sm font-medium text-gray-700 mb-1">
              Device Type *
            </label>
            <input
              id="device_type"
              type="text"
              placeholder="e.g., PLC, Sensor, Gateway"
              {...register('device_type', { required: 'Device type is required' })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            {errors.device_type && (
              <p className="mt-1 text-sm text-red-600">{errors.device_type.message}</p>
            )}
          </div>

          <div>
            <label htmlFor="protocol" className="block text-sm font-medium text-gray-700 mb-1">
              Protocol *
            </label>
            <select
              id="protocol"
              {...register('protocol', { required: 'Protocol is required' })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="opcua">OPC UA</option>
              <option value="modbus_tcp">Modbus TCP</option>
              <option value="modbus_rtu">Modbus RTU</option>
              <option value="mqtt">MQTT</option>
              <option value="ethernetip">Ethernet/IP</option>
              <option value="s7">Siemens S7</option>
            </select>
            {errors.protocol && (
              <p className="mt-1 text-sm text-red-600">{errors.protocol.message}</p>
            )}
          </div>
        </div>

        <div>
          <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-1">
            Description
          </label>
          <textarea
            id="description"
            rows={2}
            {...register('description')}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div className="flex items-center">
          <input
            id="enabled"
            type="checkbox"
            {...register('enabled')}
            className="h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
          />
          <label htmlFor="enabled" className="ml-2 block text-sm text-gray-700">
            Enabled
          </label>
        </div>
      </div>

      {/* Connection Settings */}
      <div className="space-y-4">
        <h3 className="text-sm font-semibold text-gray-700 uppercase">Connection Settings</h3>

        <div className="grid grid-cols-3 gap-4">
          <div className="col-span-2">
            <label htmlFor="ip_address" className="block text-sm font-medium text-gray-700 mb-1">
              IP Address *
            </label>
            <input
              id="ip_address"
              type="text"
              placeholder="192.168.1.100"
              {...register('ip_address', {
                required: 'IP Address is required',
                pattern: {
                  value: /^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$/,
                  message: 'Invalid IP address format',
                },
              })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            {errors.ip_address && (
              <p className="mt-1 text-sm text-red-600">{errors.ip_address.message}</p>
            )}
          </div>

          <div>
            <label htmlFor="port" className="block text-sm font-medium text-gray-700 mb-1">
              Port *
            </label>
            <input
              id="port"
              type="number"
              {...register('port', {
                required: 'Port is required',
                valueAsNumber: true,
                min: { value: 1, message: 'Port must be at least 1' },
                max: { value: 65535, message: 'Port must be at most 65535' },
              })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            {errors.port && <p className="mt-1 text-sm text-red-600">{errors.port.message}</p>}
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label htmlFor="scan_rate" className="block text-sm font-medium text-gray-700 mb-1">
              Scan Rate (ms)
            </label>
            <input
              id="scan_rate"
              type="number"
              placeholder="1000"
              {...register('scan_rate', { valueAsNumber: true })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label htmlFor="timeout" className="block text-sm font-medium text-gray-700 mb-1">
              Timeout (ms)
            </label>
            <input
              id="timeout"
              type="number"
              placeholder="5000"
              {...register('timeout', { valueAsNumber: true })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>
      </div>

      {/* Protocol Specific Configuration */}
      {selectedProtocol === 'opcua' && (
        <div className="space-y-4">
          <h3 className="text-sm font-semibold text-gray-700 uppercase">OPC UA Configuration</h3>
          <div>
            <label htmlFor="endpoint_url" className="block text-sm font-medium text-gray-700 mb-1">
              Endpoint URL
            </label>
            <input
              id="endpoint_url"
              type="text"
              placeholder="opc.tcp://192.168.1.100:4840"
              {...register('config.endpoint_url')}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>
      )}

      {(selectedProtocol === 'modbus_tcp' || selectedProtocol === 'modbus_rtu') && (
        <div className="space-y-4">
          <h3 className="text-sm font-semibold text-gray-700 uppercase">Modbus Configuration</h3>
          <div>
            <label htmlFor="unit_id" className="block text-sm font-medium text-gray-700 mb-1">
              Unit ID (Slave ID)
            </label>
            <input
              id="unit_id"
              type="number"
              placeholder="1"
              {...register('config.unit_id', { valueAsNumber: true })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>
      )}

      {selectedProtocol === 's7' && (
        <div className="space-y-4">
          <h3 className="text-sm font-semibold text-gray-700 uppercase">Siemens S7 Configuration</h3>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label htmlFor="rack" className="block text-sm font-medium text-gray-700 mb-1">
                Rack
              </label>
              <input
                id="rack"
                type="number"
                placeholder="0"
                {...register('config.rack', { valueAsNumber: true })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label htmlFor="slot" className="block text-sm font-medium text-gray-700 mb-1">
                Slot
              </label>
              <input
                id="slot"
                type="number"
                placeholder="1"
                {...register('config.slot', { valueAsNumber: true })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>
        </div>
      )}

      {selectedProtocol === 'mqtt' && (
        <div className="space-y-4">
          <h3 className="text-sm font-semibold text-gray-700 uppercase">MQTT Configuration</h3>
          <div>
            <label htmlFor="node_id" className="block text-sm font-medium text-gray-700 mb-1">
              Client ID
            </label>
            <input
              id="node_id"
              type="text"
              placeholder="mqtt-client-001"
              {...register('config.node_id')}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>
      )}

      {/* Form Actions */}
      <div className="flex justify-end space-x-3 pt-4 border-t border-gray-200">
        <button
          type="button"
          onClick={onCancel}
          disabled={isLoading}
          className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Cancel
        </button>
        <button
          type="submit"
          disabled={isLoading}
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
        >
          {isLoading && (
            <svg
              className="animate-spin h-4 w-4 text-white"
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
            >
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
              />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              />
            </svg>
          )}
          <span>{device ? 'Update Device' : 'Create Device'}</span>
        </button>
      </div>
    </form>
  );
};
