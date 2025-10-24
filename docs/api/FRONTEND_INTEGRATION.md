# Frontend Integration Guide - OptiFlow AI Platform

Complete guide for integrating React, Vue, or Angular frontends with the OptiFlow AI backend APIs.

## Table of Contents

- [Quick Start](#quick-start)
- [API Overview](#api-overview)
- [Authentication](#authentication)
- [WebSocket Real-time Data](#websocket-real-time-data)
- [REST API Endpoints](#rest-api-endpoints)
- [Data Export](#data-export)
- [Analytics](#analytics)
- [Annotations & Collaboration](#annotations--collaboration)
- [React Integration Examples](#react-integration-examples)
- [Vue Integration Examples](#vue-integration-examples)
- [Angular Integration Examples](#angular-integration-examples)

---

## Quick Start

### Base Configuration

```javascript
// Configuration
const API_BASE_URL = process.env.VITE_API_URL || 'http://localhost:8000';
const WS_BASE_URL = process.env.VITE_WS_URL || 'ws://localhost:8000';
const API_VERSION = '/api/v1';
```

### Install Dependencies

```bash
# For all frameworks
npm install axios socket.io-client

# React additional
npm install @reduxjs/toolkit react-redux

# Vue additional
npm install pinia

# Angular additional
npm install @angular/common/http
```

---

## API Overview

### Available Endpoints

| Category | Endpoint | Description |
|----------|----------|-------------|
| **Authentication** | `/api/v1/auth` | User authentication and authorization |
| **Organizations** | `/api/v1/organizations` | Organization management |
| **Sites** | `/api/v1/sites` | Site management |
| **Users** | `/api/v1/users` | User management |
| **Devices** | `/api/v1/devices` | Device management |
| **Tags** | `/api/v1/tags` | Tag (sensor) management |
| **Time Series** | `/api/v1/timeseries` | Time series data operations |
| **Alarms** | `/api/v1/alarms` | Alarm management |
| **Export** | `/api/v1/export` | Data export (CSV, JSON, Excel) |
| **Annotations** | `/api/v1/annotations` | Team collaboration and annotations |
| **Analytics** | `/api/v1/analytics` | Advanced analytics and forecasting |
| **WebSocket** | `/api/v1/ws` | Real-time data streaming |

---

## Authentication

### Login

```javascript
// POST /api/v1/auth/login
const login = async (email, password) => {
  const response = await axios.post(`${API_BASE_URL}/api/v1/auth/login`, {
    username: email,
    password: password
  });

  const { access_token, refresh_token, token_type } = response.data;

  // Store tokens
  localStorage.setItem('access_token', access_token);
  localStorage.setItem('refresh_token', refresh_token);

  return response.data;
};
```

### Axios Interceptor for Authentication

```javascript
import axios from 'axios';

const api = axios.create({
  baseURL: API_BASE_URL
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor for token refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const refreshToken = localStorage.getItem('refresh_token');
        const response = await axios.post(
          `${API_BASE_URL}/api/v1/auth/refresh`,
          { refresh_token: refreshToken }
        );

        const { access_token } = response.data;
        localStorage.setItem('access_token', access_token);

        originalRequest.headers.Authorization = `Bearer ${access_token}`;
        return api(originalRequest);
      } catch (refreshError) {
        // Redirect to login
        localStorage.clear();
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);

export default api;
```

---

## WebSocket Real-time Data

### Connection

```javascript
import { io } from 'socket.io-client';

const token = localStorage.getItem('access_token');

// Connect to WebSocket
const socket = io(`${WS_BASE_URL}/api/v1/ws/realtime?token=${token}`, {
  transports: ['websocket'],
  reconnection: true,
  reconnectionDelay: 1000,
  reconnectionAttempts: 5
});

// Connection events
socket.on('connect', () => {
  console.log('WebSocket connected');
});

socket.on('disconnect', () => {
  console.log('WebSocket disconnected');
});

socket.on('connection', (data) => {
  console.log('Connection established:', data);
});
```

### Subscribe to Tags

```javascript
// Subscribe to tag updates
const subscribeToTag = (tagId) => {
  socket.emit('message', {
    type: 'subscribe_tag',
    tag_id: tagId
  });
};

// Listen for tag updates
socket.on('tag_update', (data) => {
  console.log('Tag update received:', data);
  // {
  //   type: 'tag_update',
  //   tag_id: 'uuid',
  //   data: { value: 42.5, timestamp: '...' },
  //   timestamp: '...'
  // }
});

// Unsubscribe from tag
const unsubscribeFromTag = (tagId) => {
  socket.emit('message', {
    type: 'unsubscribe_tag',
    tag_id: tagId
  });
};
```

### Dashboard WebSocket

```javascript
const dashboardSocket = io(
  `${WS_BASE_URL}/api/v1/ws/dashboard/${dashboardId}?token=${token}`
);

// Subscribe to multiple tags at once
dashboardSocket.emit('message', {
  type: 'subscribe_tags',
  tag_ids: ['tag-1', 'tag-2', 'tag-3']
});
```

---

## REST API Endpoints

### Time Series Data

#### Query Single Tag

```javascript
// GET /api/v1/timeseries/tags/{tag_id}
const getTagData = async (tagId, startTime, endTime, aggregation, interval) => {
  const response = await api.get(`/api/v1/timeseries/tags/${tagId}`, {
    params: {
      start_time: startTime.toISOString(),
      end_time: endTime?.toISOString(),
      aggregation,  // 'mean', 'sum', 'min', 'max'
      interval      // '5m', '1h', '1d'
    }
  });

  return response.data;
};
```

#### Query Multiple Tags

```javascript
// POST /api/v1/timeseries/query
const queryMultipleTags = async (tagIds, startTime, endTime, aggregation, interval) => {
  const response = await api.post('/api/v1/timeseries/query', {
    tag_ids: tagIds,
    start_time: startTime.toISOString(),
    end_time: endTime?.toISOString(),
    aggregation,
    interval
  });

  return response.data;
};
```

#### Write Time Series Data

```javascript
// POST /api/v1/timeseries/batch
const writeTimeSeriesData = async (points) => {
  const response = await api.post('/api/v1/timeseries/batch', points);
  return response.data;
};

// Example points format
const points = [
  {
    tag_id: 'uuid',
    value: 42.5,
    timestamp: '2024-01-01T00:00:00Z',
    quality: 'good',
    device_id: 'uuid',
    site_id: 'uuid'
  }
];
```

---

## Data Export

### Export to CSV

```javascript
// POST /api/v1/export/csv
const exportToCsv = async (data, filename, columns) => {
  const response = await api.post('/api/v1/export/csv', data, {
    params: { filename, columns },
    responseType: 'blob'
  });

  // Download file
  const url = window.URL.createObjectURL(new Blob([response.data]));
  const link = document.createElement('a');
  link.href = url;
  link.setAttribute('download', filename || 'export.csv');
  document.body.appendChild(link);
  link.click();
  link.remove();
};
```

### Export Time Series to Excel

```javascript
// GET /api/v1/export/timeseries/excel
const exportTimeSeriesExcel = async (tagIds, startTime, endTime) => {
  const response = await api.get('/api/v1/export/timeseries/excel', {
    params: {
      tag_ids: tagIds,
      start_time: startTime.toISOString(),
      end_time: endTime.toISOString(),
      filename: 'timeseries_export.xlsx'
    },
    responseType: 'blob'
  });

  // Download file
  const url = window.URL.createObjectURL(new Blob([response.data]));
  const link = document.createElement('a');
  link.href = url;
  link.setAttribute('download', 'timeseries_export.xlsx');
  document.body.appendChild(link);
  link.click();
  link.remove();
};
```

---

## Analytics

### Get Statistics

```javascript
// GET /api/v1/analytics/timeseries/statistics
const getStatistics = async (tagIds, startTime, endTime) => {
  const response = await api.get('/api/v1/analytics/timeseries/statistics', {
    params: {
      tag_ids: tagIds,
      start_time: startTime.toISOString(),
      end_time: endTime?.toISOString()
    }
  });

  return response.data;
  // Returns: { mean, median, std, min, max, percentiles, ... }
};
```

### Detect Anomalies

```javascript
// GET /api/v1/analytics/timeseries/anomalies
const detectAnomalies = async (tagId, startTime, endTime, method, threshold) => {
  const response = await api.get('/api/v1/analytics/timeseries/anomalies', {
    params: {
      tag_id: tagId,
      start_time: startTime.toISOString(),
      end_time: endTime?.toISOString(),
      method,    // 'zscore', 'iqr', 'mad'
      threshold  // 3.0 for zscore
    }
  });

  return response.data;
};
```

### Calculate Trends

```javascript
// GET /api/v1/analytics/timeseries/trends
const calculateTrends = async (tagId, startTime, endTime, window) => {
  const response = await api.get('/api/v1/analytics/timeseries/trends', {
    params: {
      tag_id: tagId,
      start_time: startTime.toISOString(),
      end_time: endTime?.toISOString(),
      window: window || 10
    }
  });

  return response.data;
  // Returns: { slope, direction, strength, moving_average, ... }
};
```

### Forecast

```javascript
// GET /api/v1/analytics/timeseries/forecast
const forecast = async (tagId, startTime, endTime, periods) => {
  const response = await api.get('/api/v1/analytics/timeseries/forecast', {
    params: {
      tag_id: tagId,
      start_time: startTime.toISOString(),
      end_time: endTime?.toISOString(),
      periods: periods || 10
    }
  });

  return response.data;
};
```

---

## Annotations & Collaboration

### Create Annotation

```javascript
// POST /api/v1/annotations/
const createAnnotation = async (annotation) => {
  const response = await api.post('/api/v1/annotations/', {
    type: 'comment',  // 'comment', 'event', 'alarm', 'maintenance', 'observation', 'issue'
    priority: 'medium',  // 'low', 'medium', 'high', 'critical'
    title: 'Equipment Maintenance',
    description: 'Scheduled maintenance on Pump #3',
    start_time: new Date().toISOString(),
    end_time: null,
    device_id: 'device-uuid',
    tag_id: null,
    site_id: null,
    tags: ['maintenance', 'pump'],
    metadata: {},
    is_public: true
  });

  return response.data;
};
```

### List Annotations

```javascript
// GET /api/v1/annotations/
const listAnnotations = async (filters) => {
  const response = await api.get('/api/v1/annotations/', {
    params: {
      type: filters.type,
      device_id: filters.deviceId,
      tag_id: filters.tagId,
      start_time: filters.startTime?.toISOString(),
      end_time: filters.endTime?.toISOString(),
      is_resolved: filters.isResolved,
      skip: filters.skip || 0,
      limit: filters.limit || 100
    }
  });

  return response.data;
};
```

### Add Comment to Annotation

```javascript
// POST /api/v1/annotations/{annotation_id}/comments
const addComment = async (annotationId, comment, parentCommentId) => {
  const response = await api.post(
    `/api/v1/annotations/${annotationId}/comments`,
    {
      comment: comment,
      parent_comment_id: parentCommentId  // For threaded replies
    }
  );

  return response.data;
};
```

---

## React Integration Examples

### Custom Hook for WebSocket

```javascript
// hooks/useWebSocket.js
import { useEffect, useState } from 'react';
import { io } from 'socket.io-client';

export const useWebSocket = (tagIds = []) => {
  const [data, setData] = useState({});
  const [socket, setSocket] = useState(null);
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    const ws = io(`${WS_BASE_URL}/api/v1/ws/realtime?token=${token}`);

    ws.on('connect', () => setConnected(true));
    ws.on('disconnect', () => setConnected(false));

    ws.on('tag_update', (update) => {
      setData(prev => ({
        ...prev,
        [update.tag_id]: update.data
      }));
    });

    setSocket(ws);

    return () => ws.close();
  }, []);

  useEffect(() => {
    if (socket && connected) {
      tagIds.forEach(tagId => {
        socket.emit('message', {
          type: 'subscribe_tag',
          tag_id: tagId
        });
      });
    }
  }, [socket, connected, tagIds]);

  return { data, connected };
};
```

### Usage in Component

```javascript
import { useWebSocket } from './hooks/useWebSocket';

function Dashboard() {
  const { data, connected } = useWebSocket(['tag-1', 'tag-2', 'tag-3']);

  return (
    <div>
      <h1>Real-time Dashboard</h1>
      <p>Status: {connected ? 'Connected' : 'Disconnected'}</p>

      {Object.entries(data).map(([tagId, value]) => (
        <div key={tagId}>
          <span>{tagId}:</span>
          <span>{value?.value}</span>
        </div>
      ))}
    </div>
  );
}
```

---

## Vue Integration Examples

### Composable for WebSocket

```javascript
// composables/useWebSocket.js
import { ref, onMounted, onUnmounted, watch } from 'vue';
import { io } from 'socket.io-client';

export function useWebSocket(tagIds = []) {
  const data = ref({});
  const socket = ref(null);
  const connected = ref(false);

  onMounted(() => {
    const token = localStorage.getItem('access_token');
    socket.value = io(`${WS_BASE_URL}/api/v1/ws/realtime?token=${token}`);

    socket.value.on('connect', () => {
      connected.value = true;
    });

    socket.value.on('disconnect', () => {
      connected.value = false;
    });

    socket.value.on('tag_update', (update) => {
      data.value[update.tag_id] = update.data;
    });
  });

  watch(() => tagIds, (newTagIds) => {
    if (socket.value && connected.value) {
      newTagIds.forEach(tagId => {
        socket.value.emit('message', {
          type: 'subscribe_tag',
          tag_id: tagId
        });
      });
    }
  }, { immediate: true });

  onUnmounted(() => {
    if (socket.value) {
      socket.value.close();
    }
  });

  return { data, connected };
}
```

---

## Angular Integration Examples

### WebSocket Service

```typescript
// services/websocket.service.ts
import { Injectable } from '@angular/core';
import { io, Socket } from 'socket.io-client';
import { BehaviorSubject, Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class WebSocketService {
  private socket: Socket;
  private dataSubject = new BehaviorSubject<any>({});
  private connectedSubject = new BehaviorSubject<boolean>(false);

  constructor() {
    this.initSocket();
  }

  private initSocket(): void {
    const token = localStorage.getItem('access_token');
    this.socket = io(`${WS_BASE_URL}/api/v1/ws/realtime?token=${token}`);

    this.socket.on('connect', () => {
      this.connectedSubject.next(true);
    });

    this.socket.on('disconnect', () => {
      this.connectedSubject.next(false);
    });

    this.socket.on('tag_update', (update: any) => {
      const currentData = this.dataSubject.value;
      currentData[update.tag_id] = update.data;
      this.dataSubject.next(currentData);
    });
  }

  subscribeToTag(tagId: string): void {
    this.socket.emit('message', {
      type: 'subscribe_tag',
      tag_id: tagId
    });
  }

  unsubscribeFromTag(tagId: string): void {
    this.socket.emit('message', {
      type: 'unsubscribe_tag',
      tag_id: tagId
    });
  }

  getData(): Observable<any> {
    return this.dataSubject.asObservable();
  }

  getConnectionStatus(): Observable<boolean> {
    return this.connectedSubject.asObservable();
  }

  disconnect(): void {
    if (this.socket) {
      this.socket.close();
    }
  }
}
```

---

## Error Handling

### Global Error Handler

```javascript
const handleApiError = (error) => {
  if (error.response) {
    // Server responded with error
    const { status, data } = error.response;

    switch (status) {
      case 400:
        console.error('Bad Request:', data.detail);
        break;
      case 401:
        console.error('Unauthorized - redirecting to login');
        localStorage.clear();
        window.location.href = '/login';
        break;
      case 403:
        console.error('Forbidden:', data.detail);
        break;
      case 404:
        console.error('Not Found:', data.detail);
        break;
      case 500:
        console.error('Server Error:', data.detail);
        break;
      default:
        console.error('Error:', data.detail);
    }
  } else if (error.request) {
    // Request made but no response
    console.error('No response from server');
  } else {
    // Error in request setup
    console.error('Request error:', error.message);
  }
};
```

---

## Performance Tips

1. **Debounce API Calls**: Use debouncing for search and filter operations
2. **Pagination**: Always use pagination for large datasets
3. **WebSocket Reconnection**: Implement exponential backoff for reconnection
4. **Data Caching**: Cache API responses using React Query, SWR, or similar
5. **Lazy Loading**: Load data only when needed
6. **Compression**: Enable gzip compression on API responses

---

## API Documentation

Full interactive API documentation is available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- OpenAPI JSON: `http://localhost:8000/api/v1/openapi.json`

---

## Support

For issues or questions:
- Check API documentation at `/docs`
- Review error logs in browser console
- Contact: support@optiflow.ai
