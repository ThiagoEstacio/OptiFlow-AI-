import React, { useState, useEffect } from 'react';
import {
  Box,
  Container,
  Typography,
  Paper,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
  CircularProgress,
  Breadcrumbs,
  Link,
} from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';
import { Home, Settings } from '@mui/icons-material';
import { OPCUATagBrowser } from '../components/OPCUATagBrowser';
import axios from 'axios';

interface Device {
  id: string;
  name: string;
  protocol: string;
  status: string;
}

export const TagConfiguration: React.FC = () => {
  const [devices, setDevices] = useState<Device[]>([]);
  const [selectedDeviceId, setSelectedDeviceId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadDevices();
  }, []);

  const loadDevices = async () => {
    setLoading(true);
    setError(null);
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get<Device[]>('/api/v1/devices', {
        headers: { Authorization: `Bearer ${token}` },
      });
      // Filter for OPC UA devices (protocol can be 'OPC_UA' or 'opcua')
      const opcuaDevices = response.data.filter(d => 
        d.protocol === 'OPC_UA' || d.protocol.toLowerCase() === 'opcua'
      );
      setDevices(opcuaDevices);
      
      // Auto-select first OPC UA device
      if (opcuaDevices.length > 0) {
        setSelectedDeviceId(opcuaDevices[0].id);
      }
    } catch (err: any) {
      setError('Failed to load devices');
      console.error('Error loading devices:', err);
    } finally {
      setLoading(false);
    }
  };

  const selectedDevice = devices.find((d) => d.id === selectedDeviceId);

  return (
    <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
      {/* Breadcrumbs */}
      <Breadcrumbs sx={{ mb: 2 }}>
        <Link component={RouterLink} to="/" underline="hover" color="inherit" sx={{ display: 'flex', alignItems: 'center' }}>
          <Home sx={{ mr: 0.5 }} fontSize="small" />
          Home
        </Link>
        <Link component={RouterLink} to="/settings" underline="hover" color="inherit" sx={{ display: 'flex', alignItems: 'center' }}>
          <Settings sx={{ mr: 0.5 }} fontSize="small" />
          Settings
        </Link>
        <Typography color="text.primary">Tag Configuration</Typography>
      </Breadcrumbs>

      {/* Header */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h4" gutterBottom>
          OPC UA Tag Configuration
        </Typography>
        <Typography variant="body1" color="text.secondary" paragraph>
          Browse your OPC UA server nodes and select tags for data collection. Similar to PI System's Point Builder.
        </Typography>

        {/* Device Selector */}
        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', py: 2 }}>
            <CircularProgress />
          </Box>
        ) : error ? (
          <Alert severity="error">{error}</Alert>
        ) : devices.length === 0 ? (
          <Alert severity="info">
            No OPC UA devices found. Please configure an OPC UA device first.
          </Alert>
        ) : (
          <FormControl fullWidth sx={{ mt: 2, maxWidth: 400 }}>
            <InputLabel>Select OPC UA Device</InputLabel>
            <Select
              value={selectedDeviceId || ''}
              label="Select OPC UA Device"
              onChange={(e) => setSelectedDeviceId(e.target.value as string)}
            >
              {devices.map((device) => (
                <MenuItem key={device.id} value={device.id}>
                  {device.name} - {device.status}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        )}
      </Paper>

      {/* Tag Browser */}
      {selectedDevice && (
        <Box sx={{ height: 'calc(100vh - 350px)', minHeight: 600 }}>
          <OPCUATagBrowser
            deviceId={selectedDevice.id}
            deviceName={selectedDevice.name}
            onTagsConfigured={() => {
              // Optionally navigate or show success
              console.log('Tags configured successfully');
            }}
          />
        </Box>
      )}
    </Container>
  );
};
