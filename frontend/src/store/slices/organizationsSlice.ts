/**
 * Organizations Redux Slice
 */
import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { apiClient } from '../../api/client';
import type { Organization } from '../../types';

interface OrganizationsState {
  items: Organization[];
  loading: boolean;
  error: string | null;
}

const initialState: OrganizationsState = {
  items: [],
  loading: false,
  error: null,
};

export const fetchOrganizations = createAsyncThunk(
  'organizations/fetchAll',
  async () => {
    return await apiClient.getOrganizations();
  }
);

const organizationsSlice = createSlice({
  name: 'organizations',
  initialState,
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(fetchOrganizations.pending, (state) => {
        state.loading = true;
      })
      .addCase(fetchOrganizations.fulfilled, (state, action) => {
        state.loading = false;
        state.items = action.payload;
      })
      .addCase(fetchOrganizations.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to fetch organizations';
      });
  },
});

export default organizationsSlice.reducer;
