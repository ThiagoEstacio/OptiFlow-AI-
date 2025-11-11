/**
 * Devices Management Page with Full CRUD
 */
import React, { useEffect, useState } from 'react';
import { useAppDispatch, useAppSelector } from '../store';
import { fetchDevices, createDevice, updateDevice, deleteDevice } from '../store/slices/devicesSlice';
import { fetchSites } from '../store/slices/sitesSlice';
import { Modal } from '../components/Modal/Modal';
import { ConfirmDialog } from '../components/Modal/ConfirmDialog';
import { DeviceForm } from '../components/Forms/DeviceForm';
import { Device } from '../types';
import { showToast } from '../utils/toast';

export const DevicesPage: React.FC = () => {
  const dispatch = useAppDispatch();
  const { items: devices, loading } = useAppSelector((state) => state.devices);
  const { items: sites } = useAppSelector((state) => state.sites);

  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);
  const [selectedDevice, setSelectedDevice] = useState<Device | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    dispatch(fetchDevices());
    dispatch(fetchSites());
  }, [dispatch]);

  const handleCreate = async (data: any) => {
    setIsSubmitting(true);
    try {
      await dispatch(createDevice(data)).unwrap();
      showToast.success('Device created successfully!');
      setIsCreateModalOpen(false);
      dispatch(fetchDevices());
    } catch (error: any) {
      showToast.error(error.message || 'Failed to create device');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleEdit = async (data: any) => {
    if (!selectedDevice) return;
    setIsSubmitting(true);
    try {
      await dispatch(updateDevice({ id: selectedDevice.id, data })).unwrap();
      showToast.success('Device updated successfully!');
      setIsEditModalOpen(false);
      setSelectedDevice(null);
      dispatch(fetchDevices());
    } catch (error: any) {
      showToast.error(error.message || 'Failed to update device');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDelete = async () => {
    if (!selectedDevice) return;
    setIsSubmitting(true);
    try {
      await dispatch(deleteDevice(selectedDevice.id)).unwrap();
      showToast.success('Device deleted successfully!');
      setIsDeleteDialogOpen(false);
      setSelectedDevice(null);
      dispatch(fetchDevices());
    } catch (error: any) {
      showToast.error(error.message || 'Failed to delete device');
    } finally {
      setIsSubmitting(false);
    }
  };

  const openEditModal = (device: Device) => {
    setSelectedDevice(device);
    setIsEditModalOpen(true);
  };

  const openDeleteDialog = (device: Device) => {
    setSelectedDevice(device);
    setIsDeleteDialogOpen(true);
  };

  const filteredDevices = devices.filter((device) =>
    device.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    device.device_type.toLowerCase().includes(searchQuery.toLowerCase()) ||
    device.protocol.toLowerCase().includes(searchQuery.toLowerCase()) ||
    (device.ip_address && device.ip_address.toLowerCase().includes(searchQuery.toLowerCase()))
  );

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
        <button
          onClick={() => setIsCreateModalOpen(true)}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          Add Device
        </button>
      </div>

      {/* Search Bar */}
      <div className="bg-white rounded-lg shadow p-4">
        <input
          type="text"
          placeholder="Search devices by name, type, protocol, or IP address..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredDevices.length === 0 ? (
          <div className="col-span-full text-center py-16 bg-white rounded-lg shadow-md">
            <div className="flex flex-col items-center space-y-4">
              <div className="text-6xl">🔌</div>
              <div>
                <h3 className="text-xl font-semibold text-gray-700 mb-2">
                  {searchQuery ? 'No devices found' : 'No devices configured'}
                </h3>
                <p className="text-gray-500 mb-6">
                  {searchQuery 
                    ? 'Try adjusting your search criteria.' 
                    : 'Get started by adding your first industrial device or PLC.'}
                </p>
                {!searchQuery && (
                  <button
                    onClick={() => setIsCreateModalOpen(true)}
                    className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium inline-flex items-center space-x-2"
                  >
                    <span>➕</span>
                    <span>Add Your First Device</span>
                  </button>
                )}
              </div>
            </div>
          </div>
        ) : (
          filteredDevices.map((device) => (
            <div key={device.id} className="bg-white rounded-lg shadow-md hover:shadow-xl transition-all duration-200 overflow-hidden border border-gray-100">
              <div className="p-6">
                <div className="flex items-start justify-between mb-4">
                  <div className="flex-1">
                    <div className="flex items-center space-x-3 mb-2">
                      <div className="text-3xl">
                        {device.protocol === 'modbus_tcp' || device.protocol === 'modbus_rtu' ? '📡' : 
                         device.protocol === 'opc_ua' || device.protocol === 'opcua' ? '🔗' : 
                         device.protocol === 'mqtt' ? '📨' : 
                         device.protocol === 's7' ? '🏭' :
                         device.protocol === 'ethernetip' || device.protocol === 'ethernet_ip' ? '🌐' : '🔌'}
                      </div>
                      <div>
                        <h3 className="text-lg font-bold text-gray-900">{device.name}</h3>
                        <p className="text-xs text-gray-500 uppercase tracking-wide">{device.device_type}</p>
                      </div>
                    </div>
                    <p className="text-sm text-gray-600 mt-2">{device.description || 'No description'}</p>
                  </div>
                  <div className="flex flex-col items-end space-y-2">
                    <span
                      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                        device.status === 'connected' 
                          ? 'bg-green-100 text-green-800' 
                          : 'bg-gray-100 text-gray-600'
                      }`}
                    >
                      <span className={`w-2 h-2 rounded-full mr-1.5 ${
                        device.status === 'connected' ? 'bg-green-500 animate-pulse' : 'bg-gray-400'
                      }`}></span>
                      {device.status === 'connected' ? 'Online' : 'Offline'}
                    </span>
                    {device.enabled && (
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                        ✓ Enabled
                      </span>
                    )}
                  </div>
                </div>

                <div className="mt-4 pt-4 border-t border-gray-100 space-y-3">
                  <div className="grid grid-cols-2 gap-3 text-sm">
                    <div>
                      <span className="text-gray-500 block text-xs mb-1">Protocol</span>
                      <span className="font-semibold text-gray-900 uppercase">{device.protocol}</span>
                    </div>
                    <div>
                      <span className="text-gray-500 block text-xs mb-1">IP Address</span>
                      <span className="font-medium text-gray-900">{device.ip_address || 'N/A'}</span>
                    </div>
                    <div>
                      <span className="text-gray-500 block text-xs mb-1">Port</span>
                      <span className="font-medium text-gray-900">{device.port || 'N/A'}</span>
                    </div>
                    {device.last_seen && (
                      <div>
                        <span className="text-gray-500 block text-xs mb-1">Last Seen</span>
                        <span className="font-medium text-gray-900 text-xs">
                          {new Date(device.last_seen).toLocaleTimeString()}
                        </span>
                      </div>
                    )}
                  </div>
                </div>

                <div className="mt-4 pt-4 border-t border-gray-100 flex justify-end space-x-3">
                  <button
                    onClick={() => openEditModal(device)}
                    className="px-4 py-2 text-sm font-medium text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                  >
                    ✏️ Edit
                  </button>
                  <button
                    onClick={() => openDeleteDialog(device)}
                    className="px-4 py-2 text-sm font-medium text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                  >
                    🗑️ Delete
                  </button>
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Create Modal */}
      <Modal
        isOpen={isCreateModalOpen}
        onClose={() => !isSubmitting && setIsCreateModalOpen(false)}
        title="Create New Device"
        size="lg"
      >
        <DeviceForm
          siteId={sites[0]?.id || '4562d673-75c3-4238-9c69-69abc98eadc7'}
          onSubmit={handleCreate}
          onCancel={() => setIsCreateModalOpen(false)}
          isLoading={isSubmitting}
        />
      </Modal>

      {/* Edit Modal */}
      <Modal
        isOpen={isEditModalOpen}
        onClose={() => !isSubmitting && setIsEditModalOpen(false)}
        title="Edit Device"
        size="lg"
      >
        {selectedDevice && (
          <DeviceForm
            device={selectedDevice}
            onSubmit={handleEdit}
            onCancel={() => setIsEditModalOpen(false)}
            isLoading={isSubmitting}
          />
        )}
      </Modal>

      {/* Delete Confirmation */}
      <ConfirmDialog
        isOpen={isDeleteDialogOpen}
        onClose={() => !isSubmitting && setIsDeleteDialogOpen(false)}
        onConfirm={handleDelete}
        title="Delete Device"
        message={`Are you sure you want to delete "${selectedDevice?.name}"? This action cannot be undone.`}
        confirmText="Delete"
        cancelText="Cancel"
        variant="danger"
        isLoading={isSubmitting}
      />
    </div>
  );
};
