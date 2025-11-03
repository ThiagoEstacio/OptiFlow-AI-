import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  TextField,
  Button,
  Grid,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Alert,
  CircularProgress,
} from '@mui/material';
import { Save as SaveIcon } from '@mui/icons-material';
import axios from 'axios';

interface ManualEntryTabProps {
  siteId: number;
  dataSources: any[];
  onEntryComplete: () => void;
}

const ManualEntryTab: React.FC<ManualEntryTabProps> = ({
  siteId,
  dataSources,
  onEntryComplete,
}) => {
  const [formData, setFormData] = useState<any>({
    operation_type: '',
    operation_date: '',
    vehicle_id: '',
    product_type: '',
    net_weight_kg: '',
    gross_weight_kg: '',
    tare_weight_kg: '',
    moisture_percent: '',
    impurity_percent: '',
    loading_time_minutes: '',
    waiting_time_minutes: '',
    origin: '',
    destination: '',
    notes: '',
  });
  const [selectedDataSource, setSelectedDataSource] = useState<number | ''>('');
  const [saving, setSaving] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleChange = (field: string, value: any) => {
    setFormData({ ...formData, [field]: value });
    setError(null);
    setSuccess(false);
  };

  const handleSubmit = async () => {
    if (!selectedDataSource) {
      setError('Please select a data source');
      return;
    }

    if (!formData.operation_type || !formData.operation_date || !formData.net_weight_kg) {
      setError('Please fill in all required fields');
      return;
    }

    setSaving(true);
    setError(null);

    try {
      const token = localStorage.getItem('access_token');

      // Clean up form data - remove empty strings
      const cleanedData = Object.fromEntries(
        Object.entries(formData).filter(([_, v]) => v !== '')
      );

      await axios.post(
        `${import.meta.env.VITE_API_URL}/api/v1/gbm/manual-entry/${siteId}/${selectedDataSource}`,
        cleanedData,
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );

      setSuccess(true);
      // Reset form
      setFormData({
        operation_type: '',
        operation_date: '',
        vehicle_id: '',
        product_type: '',
        net_weight_kg: '',
        gross_weight_kg: '',
        tare_weight_kg: '',
        moisture_percent: '',
        impurity_percent: '',
        loading_time_minutes: '',
        waiting_time_minutes: '',
        origin: '',
        destination: '',
        notes: '',
      });
      setSelectedDataSource('');
      onEntryComplete();
    } catch (err: any) {
      console.error('Manual entry error:', err);
      setError(err.response?.data?.detail || 'Failed to create entry');
    } finally {
      setSaving(false);
    }
  };

  const manualDataSources = dataSources.filter((ds) => ds.source_type === 'manual');

  return (
    <Box>
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Manual Data Entry
          </Typography>
          <Typography variant="body2" color="text.secondary" paragraph>
            Enter operational data manually for individual records
          </Typography>

          <Grid container spacing={2} sx={{ mt: 2 }}>
            <Grid item xs={12}>
              <FormControl fullWidth required>
                <InputLabel>Data Source</InputLabel>
                <Select
                  value={selectedDataSource}
                  onChange={(e) => setSelectedDataSource(e.target.value as number)}
                  label="Data Source"
                >
                  {manualDataSources.map((ds) => (
                    <MenuItem key={ds.id} value={ds.id}>
                      {ds.name}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>

            <Grid item xs={12} md={6}>
              <FormControl fullWidth required>
                <InputLabel>Operation Type</InputLabel>
                <Select
                  value={formData.operation_type}
                  onChange={(e) => handleChange('operation_type', e.target.value)}
                  label="Operation Type"
                >
                  <MenuItem value="road_discharge">Road Discharge</MenuItem>
                  <MenuItem value="rail_discharge">Rail Discharge</MenuItem>
                  <MenuItem value="ship_loading">Ship Loading</MenuItem>
                  <MenuItem value="receiving">Receiving</MenuItem>
                </Select>
              </FormControl>
            </Grid>

            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                required
                label="Operation Date"
                type="datetime-local"
                value={formData.operation_date}
                onChange={(e) => handleChange('operation_date', e.target.value)}
                InputLabelProps={{ shrink: true }}
              />
            </Grid>

            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Vehicle ID"
                value={formData.vehicle_id}
                onChange={(e) => handleChange('vehicle_id', e.target.value)}
                placeholder="Truck plate, ship name, etc."
              />
            </Grid>

            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Product Type"
                value={formData.product_type}
                onChange={(e) => handleChange('product_type', e.target.value)}
                placeholder="corn, soy, wheat, etc."
              />
            </Grid>

            <Grid item xs={12} md={4}>
              <TextField
                fullWidth
                required
                label="Net Weight (kg)"
                type="number"
                value={formData.net_weight_kg}
                onChange={(e) => handleChange('net_weight_kg', e.target.value)}
              />
            </Grid>

            <Grid item xs={12} md={4}>
              <TextField
                fullWidth
                label="Gross Weight (kg)"
                type="number"
                value={formData.gross_weight_kg}
                onChange={(e) => handleChange('gross_weight_kg', e.target.value)}
              />
            </Grid>

            <Grid item xs={12} md={4}>
              <TextField
                fullWidth
                label="Tare Weight (kg)"
                type="number"
                value={formData.tare_weight_kg}
                onChange={(e) => handleChange('tare_weight_kg', e.target.value)}
              />
            </Grid>

            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Moisture (%)"
                type="number"
                value={formData.moisture_percent}
                onChange={(e) => handleChange('moisture_percent', e.target.value)}
              />
            </Grid>

            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Impurity (%)"
                type="number"
                value={formData.impurity_percent}
                onChange={(e) => handleChange('impurity_percent', e.target.value)}
              />
            </Grid>

            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Loading Time (minutes)"
                type="number"
                value={formData.loading_time_minutes}
                onChange={(e) => handleChange('loading_time_minutes', e.target.value)}
              />
            </Grid>

            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Waiting Time (minutes)"
                type="number"
                value={formData.waiting_time_minutes}
                onChange={(e) => handleChange('waiting_time_minutes', e.target.value)}
              />
            </Grid>

            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Origin"
                value={formData.origin}
                onChange={(e) => handleChange('origin', e.target.value)}
              />
            </Grid>

            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Destination"
                value={formData.destination}
                onChange={(e) => handleChange('destination', e.target.value)}
              />
            </Grid>

            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Notes"
                multiline
                rows={3}
                value={formData.notes}
                onChange={(e) => handleChange('notes', e.target.value)}
              />
            </Grid>

            <Grid item xs={12}>
              <Button
                variant="contained"
                fullWidth
                onClick={handleSubmit}
                disabled={saving}
                startIcon={saving ? <CircularProgress size={20} /> : <SaveIcon />}
              >
                {saving ? 'Saving...' : 'Save Entry'}
              </Button>
            </Grid>

            {success && (
              <Grid item xs={12}>
                <Alert severity="success">Entry saved successfully!</Alert>
              </Grid>
            )}

            {error && (
              <Grid item xs={12}>
                <Alert severity="error">{error}</Alert>
              </Grid>
            )}
          </Grid>
        </CardContent>
      </Card>
    </Box>
  );
};

export default ManualEntryTab;
