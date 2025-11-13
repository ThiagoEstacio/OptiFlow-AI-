import React, { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { Tag, DataType } from '../../types';

interface TagFormData {
  name: string;
  address: string;
  data_type: DataType;
  device_id: string;
  description?: string;
  unit?: string;
  scale_factor?: number;
  offset?: number;
  min_value?: number;
  max_value?: number;
  enabled: boolean;
  log_enabled: boolean;
}

interface TagFormProps {
  tag?: Tag;
  deviceId?: string;
  onSubmit: (data: TagFormData) => Promise<void>;
  onCancel: () => void;
  isLoading?: boolean;
}

export const TagForm: React.FC<TagFormProps> = ({
  tag,
  deviceId,
  onSubmit,
  onCancel,
  isLoading = false,
}) => {
  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
  } = useForm<TagFormData>({
    defaultValues: tag
      ? {
          name: tag.name,
          address: tag.address,
          data_type: tag.data_type,
          device_id: tag.device_id,
          description: tag.description,
          unit: tag.unit,
          scale_factor: tag.scale_factor,
          offset: tag.offset,
          min_value: tag.min_value,
          max_value: tag.max_value,
          enabled: tag.enabled,
          log_enabled: tag.log_enabled,
        }
      : ({
          device_id: deviceId || '',
          enabled: true,
          log_enabled: true,
          data_type: 'FLOAT',
          scale_factor: 1.0,
          offset: 0.0,
        } as any),
  });

  useEffect(() => {
    if (tag) {
      reset({
        name: tag.name,
        address: tag.address,
        data_type: tag.data_type,
        device_id: tag.device_id,
        description: tag.description,
        unit: tag.unit,
        scale_factor: tag.scale_factor,
        offset: tag.offset,
        min_value: tag.min_value,
        max_value: tag.max_value,
        enabled: tag.enabled,
        log_enabled: tag.log_enabled,
      });
    }
  }, [tag, reset]);

  return (
    <form onSubmit={handleSubmit(onSubmit as any)} className="space-y-6">
      {/* Basic Information */}
      <div className="space-y-4">
        <h3 className="text-sm font-semibold text-gray-700 uppercase">Basic Information</h3>

        <div>
          <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-1">
            Tag Name *
          </label>
          <input
            id="name"
            type="text"
            {...register('name', { required: 'Tag name is required' })}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          {errors.name && <p className="mt-1 text-sm text-red-600">{errors.name.message}</p>}
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label htmlFor="address" className="block text-sm font-medium text-gray-700 mb-1">
              Address *
            </label>
            <input
              id="address"
              type="text"
              placeholder="e.g., ns=2;i=1001, 40001, DB1.DBD0"
              {...register('address', { required: 'Address is required' })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            {errors.address && (
              <p className="mt-1 text-sm text-red-600">{errors.address.message}</p>
            )}
          </div>

          <div>
            <label htmlFor="data_type" className="block text-sm font-medium text-gray-700 mb-1">
              Data Type *
            </label>
            <select
              id="data_type"
              {...register('data_type', { required: 'Data type is required' })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="BOOL">Boolean</option>
              <option value="INT">Integer</option>
              <option value="FLOAT">Float</option>
              <option value="DOUBLE">Double</option>
              <option value="STRING">String</option>
              <option value="BYTE">Byte</option>
              <option value="WORD">Word</option>
              <option value="DWORD">DWord</option>
            </select>
            {errors.data_type && (
              <p className="mt-1 text-sm text-red-600">{errors.data_type.message}</p>
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

        <div>
          <label htmlFor="unit" className="block text-sm font-medium text-gray-700 mb-1">
            Unit
          </label>
          <input
            id="unit"
            type="text"
            placeholder="e.g., °C, m/s, kW"
            {...register('unit')}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
      </div>

      {/* Scaling and Limits */}
      <div className="space-y-4">
        <h3 className="text-sm font-semibold text-gray-700 uppercase">Scaling & Limits</h3>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label htmlFor="scale_factor" className="block text-sm font-medium text-gray-700 mb-1">
              Scale Factor
            </label>
            <input
              id="scale_factor"
              type="number"
              step="any"
              placeholder="1.0"
              {...register('scale_factor', { valueAsNumber: true })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label htmlFor="offset" className="block text-sm font-medium text-gray-700 mb-1">
              Offset
            </label>
            <input
              id="offset"
              type="number"
              step="any"
              placeholder="0.0"
              {...register('offset', { valueAsNumber: true })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label htmlFor="min_value" className="block text-sm font-medium text-gray-700 mb-1">
              Min Value
            </label>
            <input
              id="min_value"
              type="number"
              step="any"
              {...register('min_value', { valueAsNumber: true })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label htmlFor="max_value" className="block text-sm font-medium text-gray-700 mb-1">
              Max Value
            </label>
            <input
              id="max_value"
              type="number"
              step="any"
              {...register('max_value', { valueAsNumber: true })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>
      </div>

      {/* Options */}
      <div className="space-y-3">
        <h3 className="text-sm font-semibold text-gray-700 uppercase">Options</h3>

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

        <div className="flex items-center">
          <input
            id="log_enabled"
            type="checkbox"
            {...register('log_enabled')}
            className="h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
          />
          <label htmlFor="log_enabled" className="ml-2 block text-sm text-gray-700">
            Log to Database (Store historical data)
          </label>
        </div>
      </div>

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
          <span>{tag ? 'Update Tag' : 'Create Tag'}</span>
        </button>
      </div>
    </form>
  );
};
