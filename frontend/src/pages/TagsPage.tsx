import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Search, Filter, RefreshCw, Tag as TagIcon, Activity } from 'lucide-react';
import { tagsApi } from '../api/tags';
import { TagCategory } from '../types/tag';

export default function TagsPage() {
  const [page, setPage] = useState(1);
  const [searchQuery, setSearchQuery] = useState('');
  const [categoryFilter, setCategoryFilter] = useState<TagCategory | ''>('');
  const [activeFilter, setActiveFilter] = useState<boolean | undefined>(undefined);
  const pageSize = 20;

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['tags', page, searchQuery, categoryFilter, activeFilter],
    queryFn: () =>
      tagsApi.list({
        skip: (page - 1) * pageSize,
        limit: pageSize,
        search: searchQuery || undefined,
        category: categoryFilter || undefined,
        is_active: activeFilter,
      }),
  });

  // Query for tags with device info
  const { data: tagsWithDevices } = useQuery({
    queryKey: ['tags-with-devices', page],
    queryFn: () =>
      tagsApi.listWithDevices({
        skip: (page - 1) * pageSize,
        limit: pageSize,
      }),
  });

  const getDataTypeBadgeColor = (dataType: string) => {
    const colors: Record<string, string> = {
      boolean: 'bg-purple-100 text-purple-800',
      integer: 'bg-blue-100 text-blue-800',
      float: 'bg-green-100 text-green-800',
      double: 'bg-green-100 text-green-800',
      string: 'bg-yellow-100 text-yellow-800',
    };
    return colors[dataType] || 'bg-gray-100 text-gray-800';
  };

  const getCategoryBadgeColor = (category: string) => {
    const colors: Record<string, string> = {
      process: 'bg-blue-100 text-blue-800',
      energy: 'bg-yellow-100 text-yellow-800',
      quality: 'bg-green-100 text-green-800',
      production: 'bg-indigo-100 text-indigo-800',
      maintenance: 'bg-orange-100 text-orange-800',
      alarm: 'bg-red-100 text-red-800',
      setpoint: 'bg-purple-100 text-purple-800',
      status: 'bg-gray-100 text-gray-800',
    };
    return colors[category] || 'bg-gray-100 text-gray-800';
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Tags</h1>
          <p className="mt-2 text-sm text-gray-600">
            All available tags from connected devices - use these in your dashboards
          </p>
        </div>

        {/* Filters */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 mb-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {/* Search */}
            <div className="md:col-span-2">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => {
                    setSearchQuery(e.target.value);
                    setPage(1);
                  }}
                  placeholder="Search tags..."
                  className="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>

            {/* Category Filter */}
            <div>
              <select
                value={categoryFilter}
                onChange={(e) => {
                  setCategoryFilter(e.target.value as TagCategory | '');
                  setPage(1);
                }}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">All Categories</option>
                {Object.values(TagCategory).map((cat) => (
                  <option key={cat} value={cat}>
                    {cat.charAt(0).toUpperCase() + cat.slice(1)}
                  </option>
                ))}
              </select>
            </div>

            {/* Active Filter */}
            <div className="flex items-center gap-2">
              <select
                value={activeFilter === undefined ? '' : activeFilter ? 'true' : 'false'}
                onChange={(e) => {
                  setActiveFilter(
                    e.target.value === '' ? undefined : e.target.value === 'true'
                  );
                  setPage(1);
                }}
                className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">All Tags</option>
                <option value="true">Active Only</option>
                <option value="false">Inactive Only</option>
              </select>
              <button
                onClick={() => refetch()}
                className="p-2 border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
                title="Refresh"
              >
                <RefreshCw className="h-5 w-5 text-gray-600" />
              </button>
            </div>
          </div>
        </div>

        {/* Loading State */}
        {isLoading && (
          <div className="flex justify-center items-center h-64">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          </div>
        )}

        {/* Error State */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <p className="text-sm text-red-800">
              Error loading tags: {(error as Error).message}
            </p>
          </div>
        )}

        {/* Tags Table */}
        {data && (
          <>
            {data.tags.length === 0 ? (
              <div className="text-center py-12 bg-white rounded-lg border border-gray-200">
                <TagIcon className="mx-auto h-12 w-12 text-gray-400" />
                <h3 className="mt-2 text-sm font-medium text-gray-900">No tags found</h3>
                <p className="mt-1 text-sm text-gray-500">
                  {searchQuery || categoryFilter
                    ? 'Try adjusting your filters'
                    : 'Start by adding devices and importing tags'}
                </p>
              </div>
            ) : (
              <>
                {/* Table */}
                <div className="bg-white shadow-sm rounded-lg border border-gray-200 overflow-hidden">
                  <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                      <thead className="bg-gray-50">
                        <tr>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Tag Name
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Type
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Category
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Last Value
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Status
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Device
                          </th>
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {data.tags.map((tag) => {
                          const tagWithDevice = tagsWithDevices?.tags.find(
                            (t) => t.id === tag.id
                          );

                          return (
                            <tr key={tag.id} className="hover:bg-gray-50">
                              <td className="px-6 py-4">
                                <div className="flex items-center">
                                  <div>
                                    <div className="text-sm font-medium text-gray-900">
                                      {tag.name}
                                    </div>
                                    {tag.description && (
                                      <div className="text-xs text-gray-500 line-clamp-1">
                                        {tag.description}
                                      </div>
                                    )}
                                  </div>
                                </div>
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap">
                                <span
                                  className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getDataTypeBadgeColor(
                                    tag.data_type
                                  )}`}
                                >
                                  {tag.data_type}
                                </span>
                                {tag.unit && (
                                  <span className="ml-2 text-xs text-gray-500">{tag.unit}</span>
                                )}
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap">
                                <span
                                  className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getCategoryBadgeColor(
                                    tag.category
                                  )}`}
                                >
                                  {tag.category}
                                </span>
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap">
                                {tag.last_value ? (
                                  <div className="text-sm">
                                    <span className="font-mono text-gray-900">
                                      {tag.last_value}
                                    </span>
                                    {tag.last_timestamp && (
                                      <div className="text-xs text-gray-500">
                                        {new Date(tag.last_timestamp).toLocaleString()}
                                      </div>
                                    )}
                                  </div>
                                ) : (
                                  <span className="text-sm text-gray-400">No data</span>
                                )}
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap">
                                {tag.is_active ? (
                                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                                    <Activity className="h-3 w-3 mr-1" />
                                    Active
                                  </span>
                                ) : (
                                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                                    Inactive
                                  </span>
                                )}
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap">
                                {tagWithDevice ? (
                                  <div className="text-sm">
                                    <div className="text-gray-900">{tagWithDevice.device_name}</div>
                                    <div className="text-xs text-gray-500">
                                      {tagWithDevice.device_protocol.toUpperCase()}
                                    </div>
                                  </div>
                                ) : (
                                  <span className="text-sm text-gray-400">-</span>
                                )}
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                </div>

                {/* Pagination */}
                {data.total > pageSize && (
                  <div className="mt-6 flex items-center justify-between">
                    <div className="text-sm text-gray-700">
                      Showing <span className="font-medium">{(page - 1) * pageSize + 1}</span> to{' '}
                      <span className="font-medium">
                        {Math.min(page * pageSize, data.total)}
                      </span>{' '}
                      of <span className="font-medium">{data.total}</span> tags
                    </div>
                    <nav className="relative z-0 inline-flex rounded-md shadow-sm -space-x-px">
                      <button
                        onClick={() => setPage((p) => Math.max(1, p - 1))}
                        disabled={page === 1}
                        className="relative inline-flex items-center px-4 py-2 rounded-l-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        Previous
                      </button>
                      <span className="relative inline-flex items-center px-4 py-2 border border-gray-300 bg-white text-sm font-medium text-gray-700">
                        Page {page} of {Math.ceil(data.total / pageSize)}
                      </span>
                      <button
                        onClick={() => setPage((p) => p + 1)}
                        disabled={page >= Math.ceil(data.total / pageSize)}
                        className="relative inline-flex items-center px-4 py-2 rounded-r-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        Next
                      </button>
                    </nav>
                  </div>
                )}
              </>
            )}
          </>
        )}
      </div>
    </div>
  );
}
