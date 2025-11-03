/**
 * Devices Redux Slice
 */
import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import { apiClient } from '../../api/client';
import type { Device } from '../../types';

interface DevicesState {
  items: Device[];
  selectedDevice: Device | null;
  loading: boolean;
  error: string | null;
}

const initialState: DevicesState = {
  items: [],
  selectedDevice: null,
  loading: false,
  error: null,
};

export const fetchDevices = createAsyncThunk(
  'devices/fetchAll',
  async (params?: { site_id?: string }) => {
    return await apiClient.getDevices(params);
  }
);

export const fetchDevice = createAsyncThunk(
  'devices/fetchOne',
  async (id: string) => {
    return await apiClient.getDevice(id);
  }
);

export const createDevice = createAsyncThunk(
  'devices/create',
  async (data: Partial<Device>) => {
    return await apiClient.createDevice(data);
  }
);

export const updateDevice = createAsyncThunk(
  'devices/update',
  async ({ id, data }: { id: string; data: Partial<Device> }) => {
    return await apiClient.updateDevice(id, data);
  }
);

export const deleteDevice = createAsyncThunk(
  'devices/delete',
  async (id: string) => {
    await apiClient.deleteDevice(id);
    return id;
  }
);

const devicesSlice = createSlice({
  name: 'devices',
  initialState,
  reducers: {
    selectDevice: (state, action: PayloadAction<Device | null>) => {
      state.selectedDevice = action.payload;
    },
    clearError: (state) => {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchDevices.pending, (state) => {
        state.loading = true;
      })
      .addCase(fetchDevices.fulfilled, (state, action) => {
        state.loading = false;
        state.items = action.payload;
      })
      .addCase(fetchDevices.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to fetch devices';
      })
      .addCase(fetchDevice.fulfilled, (state, action) => {
        state.selectedDevice = action.payload;
      })
      .addCase(createDevice.fulfilled, (state, action) => {
        state.items.push(action.payload);
      })
      .addCase(updateDevice.fulfilled, (state, action) => {
        const index = state.items.findIndex((d) => d.id === action.payload.id);
        if (index !== -1) {
          state.items[index] = action.payload;
        }
      })
      .addCase(deleteDevice.fulfilled, (state, action) => {
        state.items = state.items.filter((d) => d.id !== action.payload);
      });
  },
});

export const { selectDevice, clearError } = devicesSlice.actions;
export default devicesSlice.reducer;
