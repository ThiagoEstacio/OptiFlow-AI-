/**
 * Tags Redux Slice
 */
import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { apiClient } from '../../api/client';
import type { Tag, TimeseriesDataPoint } from '../../types';

interface TagsState {
  items: Tag[];
  selectedTag: Tag | null;
  tagData: Record<string, TimeseriesDataPoint[]>;
  loading: boolean;
  error: string | null;
}

const initialState: TagsState = {
  items: [],
  selectedTag: null,
  tagData: {},
  loading: false,
  error: null,
};

export const fetchTags = createAsyncThunk(
  'tags/fetchAll',
  async (params?: { device_id?: string }) => {
    return await apiClient.getTags(params);
  }
);

export const fetchTagData = createAsyncThunk(
  'tags/fetchData',
  async (params: { tag_id: string; range?: string }) => {
    const data = await apiClient.getTagData({ ...params, range: params.range || '1h' });
    return { tag_id: params.tag_id, data };
  }
);

export const createTag = createAsyncThunk(
  'tags/create',
  async (data: Partial<Tag>) => {
    return await apiClient.createTag(data);
  }
);

export const updateTag = createAsyncThunk(
  'tags/update',
  async ({ id, data }: { id: string; data: Partial<Tag> }) => {
    return await apiClient.updateTag(id, data);
  }
);

export const deleteTag = createAsyncThunk(
  'tags/delete',
  async (id: string) => {
    await apiClient.deleteTag(id);
    return id;
  }
);

const tagsSlice = createSlice({
  name: 'tags',
  initialState,
  reducers: {
    selectTag: (state, action) => {
      state.selectedTag = action.payload;
    },
    updateTagValue: (state, action) => {
      const { tag_id, value, timestamp, quality } = action.payload;
      // Update in tagData
      if (state.tagData[tag_id]) {
        state.tagData[tag_id].push({ value, timestamp, quality });
        // Keep only last 100 points
        if (state.tagData[tag_id].length > 100) {
          state.tagData[tag_id].shift();
        }
      }
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchTags.pending, (state) => {
        state.loading = true;
      })
      .addCase(fetchTags.fulfilled, (state, action) => {
        state.loading = false;
        state.items = action.payload;
      })
      .addCase(fetchTags.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to fetch tags';
      })
      .addCase(fetchTagData.fulfilled, (state, action) => {
        state.tagData[action.payload.tag_id] = action.payload.data;
      })
      .addCase(createTag.fulfilled, (state, action) => {
        state.items.push(action.payload);
      })
      .addCase(updateTag.fulfilled, (state, action) => {
        const index = state.items.findIndex((t) => t.id === action.payload.id);
        if (index !== -1) {
          state.items[index] = action.payload;
        }
      })
      .addCase(deleteTag.fulfilled, (state, action) => {
        state.items = state.items.filter((t) => t.id !== action.payload);
      });
  },
});

export const { selectTag, updateTagValue } = tagsSlice.actions;
export default tagsSlice.reducer;
