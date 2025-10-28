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
          <div className="col-span-full text-center py-12 bg-white rounded-lg shadow">
            <p className="text-gray-500">
              {searchQuery ? 'No devices found matching your search.' : 'No devices found. Click "Add Device" to create one.'}
            </p>
          </div>
        ) : (
          filteredDevices.map((device) => (
            <div key={device.id} className="bg-white rounded-lg shadow p-6 hover:shadow-lg transition-shadow">
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                  <h3 className="text-lg font-semibold text-gray-900">{device.name}</h3>
                  <p className="text-sm text-gray-500 mt-1">{device.description || device.device_type}</p>
                </div>
                <span
                  className={`w-3 h-3 rounded-full flex-shrink-0 ${
                    device.status === 'connected' ? 'bg-green-500' : 'bg-gray-300'
                  }`}
                  title={device.status === 'connected' ? 'Connected' : 'Disconnected'}
                ></span>
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
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Status:</span>
                  <span className={`font-medium ${device.enabled ? 'text-green-600' : 'text-gray-400'}`}>
                    {device.enabled ? 'Enabled' : 'Disabled'}
                  </span>
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
                <button
                  onClick={() => openEditModal(device)}
                  className="text-blue-600 hover:text-blue-800 text-sm font-medium"
                >
                  Edit
                </button>
                <button
                  onClick={() => openDeleteDialog(device)}
                  className="text-red-600 hover:text-red-800 text-sm font-medium"
                >
                  Delete
                </button>
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
          siteId={sites[0]?.id}
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
