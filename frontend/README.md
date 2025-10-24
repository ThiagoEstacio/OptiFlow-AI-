# OptiFlow AI Frontend

React + TypeScript + Vite frontend for OptiFlow AI Platform

## Features

### ✅ Implemented

- **Real-time WebSocket Integration**
  - Live data streaming
  - Tag and device subscriptions
  - Dashboard-specific connections

- **Interactive Dashboards**
  - Real-time line charts with Recharts
  - Stat cards with trends
  - Responsive layout

- **Advanced Analytics**
  - Statistical analysis panel
  - Anomaly detection with multiple methods
  - Trend analysis
  - Forecasting capabilities

- **Authentication**
  - JWT-based authentication
  - Token refresh handling
  - Protected routes

- **Modern UI/UX**
  - Tailwind CSS styling
  - Responsive design
  - Loading states
  - Error handling

## Tech Stack

- **React 18.2** - UI library
- **TypeScript 5.3** - Type safety
- **Vite 5.0** - Build tool
- **React Router 6** - Routing
- **Socket.IO Client** - WebSocket
- **Recharts** - Charts
- **Axios** - HTTP client
- **Tailwind CSS** - Styling
- **Lucide React** - Icons

## Quick Start

### Install Dependencies

```bash
npm install
```

### Environment Variables

Create `.env` file:

```bash
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
```

### Development

```bash
npm run dev
```

Access at: http://localhost:5173

### Build for Production

```bash
npm run build
```

### Preview Production Build

```bash
npm run preview
```

## Project Structure

```
src/
├── api/                   # API configuration and client
│   ├── client.ts         # Axios instance with interceptors
│   └── config.ts         # API endpoints and config
├── components/
│   ├── analytics/        # Analytics components
│   │   ├── StatisticsPanel.tsx
│   │   └── AnomalyDetector.tsx
│   ├── common/           # Reusable components
│   │   ├── LoadingSpinner.tsx
│   │   ├── ErrorMessage.tsx
│   │   └── StatCard.tsx
│   ├── dashboard/        # Dashboard components
│   │   └── RealTimeChart.tsx
│   └── layout/           # Layout components
│       ├── MainLayout.tsx
│       ├── Sidebar.tsx
│       └── Header.tsx
├── hooks/                # Custom React hooks
│   ├── useAuth.ts       # Authentication
│   ├── useWebSocket.ts  # Real-time data
│   ├── useAnalytics.ts  # Analytics APIs
│   └── useTimeSeries.ts # Time series data
├── pages/                # Page components
│   ├── DashboardPage.tsx
│   └── LoginPage.tsx
├── types/                # TypeScript types
│   └── index.ts
└── App.tsx              # Main application

```

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint
- `npm run lint:fix` - Fix ESLint errors
- `npm run format` - Format code with Prettier
- `npm run type-check` - Check TypeScript types
- `npm run test` - Run tests
- `npm run coverage` - Generate coverage report

## Features in Detail

### WebSocket Integration

```typescript
import { useWebSocket } from './hooks/useWebSocket';

function MyComponent() {
  const { tagData, connected, subscribeToTag } = useWebSocket();

  useEffect(() => {
    subscribeToTag('tag-id-123');
  }, []);

  return (
    <div>
      {connected ? 'Connected' : 'Disconnected'}
      Value: {tagData['tag-id-123']?.value}
    </div>
  );
}
```

### Analytics

```typescript
import { useStatistics } from './hooks/useAnalytics';

function AnalyticsPanel() {
  const { data, fetchStatistics } = useStatistics();

  useEffect(() => {
    fetchStatistics(['tag-1', 'tag-2'], new Date(), new Date());
  }, []);

  return <div>Mean: {data?.mean}</div>;
}
```

### Real-time Charts

```typescript
import { RealTimeChart } from './components/dashboard/RealTimeChart';

function Dashboard() {
  return (
    <RealTimeChart
      tagIds={['tag-1', 'tag-2']}
      title="Sensor Data"
      height={400}
      maxDataPoints={50}
    />
  );
}
```

## API Integration

All API calls go through Axios with:
- Automatic token injection
- Token refresh on 401
- Error handling
- TypeScript types

## Components

### StatCard
Display key metrics with trends

### RealTimeChart
Live updating line chart with WebSocket

### StatisticsPanel
Complete statistical analysis

### AnomalyDetector
Detect and visualize anomalies

### LoadingSpinner
Loading state indicator

### ErrorMessage
Error display with retry

## Customization

### Colors
Edit `tailwind.config.js` for theme colors

### API Endpoints
Edit `src/api/config.ts` for API URLs

### WebSocket Events
Customize in `src/hooks/useWebSocket.ts`

## Troubleshooting

### WebSocket not connecting
- Check VITE_WS_URL in .env
- Verify backend WebSocket is running
- Check browser console for errors

### API calls failing
- Verify VITE_API_URL in .env
- Check network tab for request details
- Ensure backend is running

### Build errors
- Clear node_modules and reinstall
- Check TypeScript errors with `npm run type-check`
- Verify all dependencies are installed

## Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

## Performance

- Code splitting with React.lazy
- Optimized re-renders
- Debounced API calls
- Memoized components

## Security

- JWT token storage in localStorage
- Automatic token refresh
- Protected routes
- CORS handling

## Next Steps

### Short Term
- [ ] Add more chart types (bar, pie, gauge)
- [ ] Implement data export UI
- [ ] Build annotations interface
- [ ] Add device management pages

### Medium Term
- [ ] Add Redux for state management
- [ ] Implement offline support
- [ ] Add PWA capabilities
- [ ] Build mobile responsive views

### Long Term
- [ ] Multi-language support
- [ ] Dark mode
- [ ] Advanced customization
- [ ] Report builder

## Contributing

See main project CONTRIBUTING.md

## License

Proprietary - All rights reserved

---

Built with ❤️ using React, TypeScript, and Vite
