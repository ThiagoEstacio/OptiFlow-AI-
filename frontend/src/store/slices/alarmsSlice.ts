/**
 * Alarms Redux Slice
 */
import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { apiClient } from '../../api/client';
import type { AlarmEvent } from '../../types';

interface AlarmsState {
  activeAlarms: AlarmEvent[];
  loading: boolean;
  error: string | null;
}

const initialState: AlarmsState = {
  activeAlarms: [],
  loading: false,
  error: null,
};

export const fetchActiveAlarms = createAsyncThunk(
  'alarms/fetchActive',
  async () => {
    return await apiClient.getAlarmEvents({ active: true });
  }
);

export const acknowledgeAlarm = createAsyncThunk(
  'alarms/acknowledge',
  async (alarmId: string) => {
    await apiClient.acknowledgeAlarm(alarmId);
    return alarmId;
  }
);

const alarmsSlice = createSlice({
  name: 'alarms',
  initialState,
  reducers: {
    addAlarm: (state, action) => {
      state.activeAlarms.unshift(action.payload);
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchActiveAlarms.pending, (state) => {
        state.loading = true;
      })
      .addCase(fetchActiveAlarms.fulfilled, (state, action) => {
        state.loading = false;
        state.activeAlarms = action.payload;
      })
      .addCase(fetchActiveAlarms.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to fetch alarms';
      })
      .addCase(acknowledgeAlarm.fulfilled, (state, action) => {
        state.activeAlarms = state.activeAlarms.filter((a) => a.id !== action.payload);
      });
  },
});

export const { addAlarm } = alarmsSlice.actions;
export default alarmsSlice.reducer;
