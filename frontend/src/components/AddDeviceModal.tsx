import React, { useState } from 'react';
import { X, Loader2, Check, AlertCircle, Search } from 'lucide-react';
import { useMutation } from '@tanstack/react-query';
import { devicesApi } from '../api/devices';
import { DeviceProtocol, type BrowsedTag } from '../types/device';

interface AddDeviceModalProps {
  onClose: () => void;
  onSuccess: () => void;
}

type Step = 'connection' | 'browse' | 'import';

export default function AddDeviceModal({ onClose, onSuccess }: AddDeviceModalProps) {
  const [step, setStep] = useState<Step>('connection');
  const [name, setName] = useState('');
  const [protocol, setProtocol] = useState<DeviceProtocol>(DeviceProtocol.OPC_UA);
  const [endpoint, setEndpoint] = useState('opc.tcp://localhost:4840');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [connectionTested, setConnectionTested] = useState(false);
  const [browsedTags, setBrowsedTags] = useState<BrowsedTag[]>([]);
  const [selectedTags, setSelectedTags] = useState<Set<string>>(new Set());
  const [searchQuery, setSearchQuery] = useState('');
  const [deviceId, setDeviceId] = useState<string>('');

  // Test connection mutation
  const testConnectionMutation = useMutation({
    mutationFn: () =>
      devicesApi.testConnection({
        protocol,
        connection_config: { endpoint, username, password },
      }),
    onSuccess: (data) => {
      if (data.success) {
        setConnectionTested(true);
      }
    },
  });

  // Browse tags mutation
  const browseTagsMutation = useMutation({
    mutationFn: () =>
      devicesApi.browseTags({
        protocol,
        connection_config: { endpoint, username, password },
        max_depth: 10,
      }),
    onSuccess: (data) => {
      if (data.success) {
        setBrowsedTags(data.tags);
        setStep('browse');
      }
    },
  });

  // Create device mutation
  const createDeviceMutation = useMutation({
    mutationFn: () =>
      devicesApi.create({
        site_id: '00000000-0000-0000-0000-000000000001', // TODO: Get from context/props
        name,
        protocol,
        connection_config: { endpoint, username, password },
        description: `OPC UA device at ${endpoint}`,
      }),
    onSuccess: (device) => {
      setDeviceId(device.id);
      setStep('import');
    },
  });

  // Import tags mutation
  const importTagsMutation = useMutation({
    mutationFn: () => {
      const tagsToImport = browsedTags.filter((tag) =>
        selectedTags.has(tag.node_id)
      );
      return devicesApi.importTags({
        device_id: deviceId,
        tags: tagsToImport,
        auto_activate: true,
        category: 'process',
      });
    },
    onSuccess: () => {
      onSuccess();
    },
  });

  const handleTestConnection = () => {
    if (!endpoint) return;
    testConnectionMutation.mutate();
  };

  const handleBrowseTags = () => {
    if (!name) {
      alert('Please enter a device name');
      return;
    }
    createDeviceMutation.mutate();
    browseTagsMutation.mutate();
  };

  const handleImportTags = () => {
    if (selectedTags.size === 0) {
      alert('Please select at least one tag to import');
      return;
    }
    importTagsMutation.mutate();
  };

  const toggleTagSelection = (nodeId: string) => {
    const newSelected = new Set(selectedTags);
    if (newSelected.has(nodeId)) {
      newSelected.delete(nodeId);
    } else {
      newSelected.add(nodeId);
    }
    setSelectedTags(newSelected);
  };

  const toggleSelectAll = () => {
    if (selectedTags.size === filteredTags.length) {
      setSelectedTags(new Set());
    } else {
      setSelectedTags(new Set(filteredTags.map((t) => t.node_id)));
    }
  };

  const filteredTags = browsedTags.filter(
    (tag) =>
      tag.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      tag.full_path.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">Add OPC UA Device</h3>
            <p className="text-sm text-gray-500 mt-1">
              {step === 'connection' && 'Connect to OPC UA server'}
              {step === 'browse' && 'Browse and select tags'}
              {step === 'import' && 'Importing tags...'}
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-500 transition-colors"
          >
            <X className="h-6 w-6" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto px-6 py-4">
          {/* Step 1: Connection */}
          {step === 'connection' && (
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Device Name *
                </label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g., PLC Simulator 1"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Protocol
                </label>
                <select
                  value={protocol}
                  onChange={(e) => setProtocol(e.target.value as DeviceProtocol)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value={DeviceProtocol.OPC_UA}>OPC UA</option>
                  <option value={DeviceProtocol.MODBUS_TCP} disabled>
                    Modbus TCP (Coming Soon)
                  </option>
                  <option value={DeviceProtocol.MQTT} disabled>
                    MQTT (Coming Soon)
                  </option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  OPC UA Endpoint *
                </label>
                <input
                  type="text"
                  value={endpoint}
                  onChange={(e) => setEndpoint(e.target.value)}
                  placeholder="opc.tcp://localhost:4840"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Username (Optional)
                  </label>
                  <input
                    type="text"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    placeholder="Username"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Password (Optional)
                  </label>
                  <input
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="Password"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>

              {/* Test Connection Result */}
              {testConnectionMutation.isSuccess && testConnectionMutation.data && (
                <div
                  className={`p-4 rounded-md ${
                    testConnectionMutation.data.success
                      ? 'bg-green-50 border border-green-200'
                      : 'bg-red-50 border border-red-200'
                  }`}
                >
                  <div className="flex items-start">
                    {testConnectionMutation.data.success ? (
                      <Check className="h-5 w-5 text-green-600 mt-0.5 mr-3" />
                    ) : (
                      <AlertCircle className="h-5 w-5 text-red-600 mt-0.5 mr-3" />
                    )}
                    <div className="flex-1">
                      <h4
                        className={`text-sm font-medium ${
                          testConnectionMutation.data.success
                            ? 'text-green-800'
                            : 'text-red-800'
                        }`}
                      >
                        {testConnectionMutation.data.success
                          ? 'Connection Successful'
                          : 'Connection Failed'}
                      </h4>
                      {testConnectionMutation.data.success ? (
                        <p className="text-sm text-green-700 mt-1">
                          {testConnectionMutation.data.message}
                        </p>
                      ) : (
                        <p className="text-sm text-red-700 mt-1">
                          {testConnectionMutation.data.error}
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Step 2: Browse Tags */}
          {step === 'browse' && (
            <div className="space-y-4">
              <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
                <p className="text-sm text-blue-800">
                  Found <strong>{browsedTags.length}</strong> tags. Select the tags you want
                  to import.
                </p>
              </div>

              {/* Search */}
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Search tags..."
                  className="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              {/* Select All */}
              <div className="flex items-center justify-between py-2 border-b border-gray-200">
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={selectedTags.size === filteredTags.length}
                    onChange={toggleSelectAll}
                    className="h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                  />
                  <span className="ml-2 text-sm font-medium text-gray-700">
                    Select All ({selectedTags.size} selected)
                  </span>
                </label>
              </div>

              {/* Tags List */}
              <div className="space-y-2 max-h-96 overflow-y-auto">
                {filteredTags.map((tag) => (
                  <div
                    key={tag.node_id}
                    className="flex items-start p-3 border border-gray-200 rounded-md hover:bg-gray-50"
                  >
                    <input
                      type="checkbox"
                      checked={selectedTags.has(tag.node_id)}
                      onChange={() => toggleTagSelection(tag.node_id)}
                      className="h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500 mt-1"
                    />
                    <div className="ml-3 flex-1">
                      <div className="flex items-start justify-between">
                        <div>
                          <p className="text-sm font-medium text-gray-900">{tag.name}</p>
                          <p className="text-xs text-gray-500 mt-0.5">{tag.full_path}</p>
                        </div>
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800">
                          {tag.data_type}
                        </span>
                      </div>
                      {tag.current_value && (
                        <p className="text-xs text-gray-600 mt-1">
                          Current: {tag.current_value}
                        </p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Step 3: Importing */}
          {step === 'import' && (
            <div className="flex flex-col items-center justify-center py-12">
              {importTagsMutation.isPending ? (
                <>
                  <Loader2 className="h-12 w-12 text-blue-600 animate-spin" />
                  <p className="mt-4 text-sm text-gray-600">
                    Importing {selectedTags.size} tags...
                  </p>
                </>
              ) : importTagsMutation.isSuccess ? (
                <>
                  <div className="h-12 w-12 bg-green-100 rounded-full flex items-center justify-center">
                    <Check className="h-6 w-6 text-green-600" />
                  </div>
                  <p className="mt-4 text-sm font-medium text-gray-900">
                    Successfully imported {importTagsMutation.data?.imported} tags
                  </p>
                  {importTagsMutation.data?.skipped! > 0 && (
                    <p className="text-sm text-gray-600">
                      {importTagsMutation.data?.skipped} tags were skipped (already exist)
                    </p>
                  )}
                </>
              ) : null}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-gray-200 flex justify-between">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            Cancel
          </button>

          <div className="flex gap-3">
            {step === 'connection' && (
              <>
                <button
                  onClick={handleTestConnection}
                  disabled={!endpoint || testConnectionMutation.isPending}
                  className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed inline-flex items-center"
                >
                  {testConnectionMutation.isPending ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      Testing...
                    </>
                  ) : (
                    'Test Connection'
                  )}
                </button>
                <button
                  onClick={handleBrowseTags}
                  disabled={
                    !connectionTested ||
                    !name ||
                    browseTagsMutation.isPending ||
                    createDeviceMutation.isPending
                  }
                  className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed inline-flex items-center"
                >
                  {browseTagsMutation.isPending || createDeviceMutation.isPending ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      Browsing...
                    </>
                  ) : (
                    'Browse Tags'
                  )}
                </button>
              </>
            )}

            {step === 'browse' && (
              <button
                onClick={handleImportTags}
                disabled={selectedTags.size === 0}
                className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Import {selectedTags.size} Tags
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
