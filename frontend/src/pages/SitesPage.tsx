/**
 * Sites Management Page with Full CRUD
 */
import React, { useEffect, useState } from 'react';
import { useAppDispatch, useAppSelector } from '../store';
import { fetchSites, createSite, updateSite, deleteSite } from '../store/slices/sitesSlice';
import { Modal } from '../components/Modal/Modal';
import { ConfirmDialog } from '../components/Modal/ConfirmDialog';
import { SiteForm } from '../components/Forms/SiteForm';
import { Site } from '../types';
import { showToast } from '../utils/toast';

export const SitesPage: React.FC = () => {
  const dispatch = useAppDispatch();
  const { items: sites, loading } = useAppSelector((state) => state.sites);
  const { user } = useAppSelector((state) => state.auth);

  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);
  const [selectedSite, setSelectedSite] = useState<Site | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    dispatch(fetchSites());
  }, [dispatch]);

  const handleCreate = async (data: any) => {
    setIsSubmitting(true);
    try {
      await dispatch(createSite(data)).unwrap();
      showToast.success('Site created successfully!');
      setIsCreateModalOpen(false);
      dispatch(fetchSites());
    } catch (error: any) {
      showToast.error(error.message || 'Failed to create site');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleEdit = async (data: any) => {
    if (!selectedSite) return;
    setIsSubmitting(true);
    try {
      await dispatch(updateSite({ id: selectedSite.id, data })).unwrap();
      showToast.success('Site updated successfully!');
      setIsEditModalOpen(false);
      setSelectedSite(null);
      dispatch(fetchSites());
    } catch (error: any) {
      showToast.error(error.message || 'Failed to update site');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDelete = async () => {
    if (!selectedSite) return;
    setIsSubmitting(true);
    try {
      await dispatch(deleteSite(selectedSite.id)).unwrap();
      showToast.success('Site deleted successfully!');
      setIsDeleteDialogOpen(false);
      setSelectedSite(null);
      dispatch(fetchSites());
    } catch (error: any) {
      showToast.error(error.message || 'Failed to delete site');
    } finally {
      setIsSubmitting(false);
    }
  };

  const openEditModal = (site: Site) => {
    setSelectedSite(site);
    setIsEditModalOpen(true);
  };

  const openDeleteDialog = (site: Site) => {
    setSelectedSite(site);
    setIsDeleteDialogOpen(true);
  };

  const filteredSites = sites.filter((site) =>
    site.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    site.site_type.toLowerCase().includes(searchQuery.toLowerCase()) ||
    (site.city && site.city.toLowerCase().includes(searchQuery.toLowerCase())) ||
    (site.country && site.country.toLowerCase().includes(searchQuery.toLowerCase()))
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
          <h1 className="text-3xl font-bold text-gray-900">Sites</h1>
          <p className="text-gray-600 mt-1">Manage your SmartPort sites</p>
        </div>
        <button
          onClick={() => setIsCreateModalOpen(true)}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          Add Site
        </button>
      </div>

      {/* Search Bar */}
      <div className="bg-white rounded-lg shadow p-4">
        <input
          type="text"
          placeholder="Search sites by name, type, or location..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Name
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Type
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Location
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Status
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {filteredSites.length === 0 ? (
              <tr>
                <td colSpan={5} className="px-6 py-12 text-center text-gray-500">
                  {searchQuery ? 'No sites found matching your search.' : 'No sites found. Click "Add Site" to create one.'}
                </td>
              </tr>
            ) : (
              filteredSites.map((site) => (
                <tr key={site.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm font-medium text-gray-900">{site.name}</div>
                    <div className="text-sm text-gray-500">{site.description}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-blue-100 text-blue-800">
                      {site.site_type}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {site.city && site.country ? `${site.city}, ${site.country}` : site.city || site.country || '-'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span
                      className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                        site.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                      }`}
                    >
                      {site.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <button
                      onClick={() => openEditModal(site)}
                      className="text-blue-600 hover:text-blue-900 mr-3"
                    >
                      Edit
                    </button>
                    <button
                      onClick={() => openDeleteDialog(site)}
                      className="text-red-600 hover:text-red-900"
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Create Modal */}
      <Modal
        isOpen={isCreateModalOpen}
        onClose={() => !isSubmitting && setIsCreateModalOpen(false)}
        title="Create New Site"
        size="lg"
      >
        <SiteForm
          organizationId={user?.organization_id}
          onSubmit={handleCreate}
          onCancel={() => setIsCreateModalOpen(false)}
          isLoading={isSubmitting}
        />
      </Modal>

      {/* Edit Modal */}
      <Modal
        isOpen={isEditModalOpen}
        onClose={() => !isSubmitting && setIsEditModalOpen(false)}
        title="Edit Site"
        size="lg"
      >
        {selectedSite && (
          <SiteForm
            site={selectedSite}
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
        title="Delete Site"
        message={`Are you sure you want to delete "${selectedSite?.name}"? This action cannot be undone.`}
        confirmText="Delete"
        cancelText="Cancel"
        variant="danger"
        isLoading={isSubmitting}
      />
    </div>
  );
};
