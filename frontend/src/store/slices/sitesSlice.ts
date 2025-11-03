/**
 * Sites Redux Slice
 */
import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import { apiClient } from '../../api/client';
import type { Site } from '../../types';

interface SitesState {
  items: Site[];
  selectedSite: Site | null;
  loading: boolean;
  error: string | null;
}

const initialState: SitesState = {
  items: [],
  selectedSite: null,
  loading: false,
  error: null,
};

export const fetchSites = createAsyncThunk(
  'sites/fetchAll',
  async (params?: { organization_id?: string; site_type?: string }) => {
    return await apiClient.getSites(params);
  }
);

export const fetchSite = createAsyncThunk(
  'sites/fetchOne',
  async (id: string) => {
    return await apiClient.getSite(id);
  }
);

export const createSite = createAsyncThunk(
  'sites/create',
  async (data: Partial<Site>) => {
    return await apiClient.createSite(data);
  }
);

export const updateSite = createAsyncThunk(
  'sites/update',
  async ({ id, data }: { id: string; data: Partial<Site> }) => {
    return await apiClient.updateSite(id, data);
  }
);

export const deleteSite = createAsyncThunk(
  'sites/delete',
  async (id: string) => {
    await apiClient.deleteSite(id);
    return id;
  }
);

const sitesSlice = createSlice({
  name: 'sites',
  initialState,
  reducers: {
    selectSite: (state, action: PayloadAction<Site | null>) => {
      state.selectedSite = action.payload;
    },
    clearError: (state) => {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchSites.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchSites.fulfilled, (state, action) => {
        state.loading = false;
        state.items = action.payload;
      })
      .addCase(fetchSites.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to fetch sites';
      })
      .addCase(fetchSite.fulfilled, (state, action) => {
        state.selectedSite = action.payload;
      })
      .addCase(createSite.fulfilled, (state, action) => {
        state.items.push(action.payload);
      })
      .addCase(updateSite.fulfilled, (state, action) => {
        const index = state.items.findIndex((s) => s.id === action.payload.id);
        if (index !== -1) {
          state.items[index] = action.payload;
        }
        if (state.selectedSite?.id === action.payload.id) {
          state.selectedSite = action.payload;
        }
      })
      .addCase(deleteSite.fulfilled, (state, action) => {
        state.items = state.items.filter((s) => s.id !== action.payload);
        if (state.selectedSite?.id === action.payload) {
          state.selectedSite = null;
        }
      });
  },
});

export const { selectSite, clearError } = sitesSlice.actions;
export default sitesSlice.reducer;
