# SmartPort Frontend - Quick Start Guide

## What Was Implemented

### UI Component Library (Week 3 Complete)

**Base Components:**
- `Button` - 5 variants, 3 sizes, loading states, icon support
- `Card` - Container with header, body, footer sections
- `Badge` - 6 color variants with animated dots
- `Input` - Form input with validation states and icons
- `ProgressBar` - Single and multi-segment progress bars
- `Skeleton` - Loading placeholders with pre-built layouts
- `Tooltip` - Accessible tooltips built on Radix UI

**SmartPort Components:**
- `KPICard` - Key performance indicator cards with trends
- `BerthCard` - Berth status display with vessel information
- `EquipmentCard` - Equipment health monitoring cards
- `StatusIndicator` - Smart status badges with auto-coloring

**Layout Components:**
- `Header` - Top navigation with search and notifications
- `Sidebar` - Collapsible navigation sidebar
- `MainLayout` - Complete application layout wrapper

### Pages

**Port Dashboard (/)** - Main dashboard featuring:
- 4 KPI cards (Throughput, Efficiency, Vessels, Alerts)
- Real-time performance chart (48h loading rate + energy)
- Live berth status cards
- Critical equipment monitoring
- Operations summary

### API Integration

**TypeScript Types:** Complete type system matching backend schemas
- Vessel, Berth, LoadingOperation, Equipment types
- Analytics and KPI response types
- Search parameters and filters

**API Services:**
- `portAPI.vessels` - Vessel CRUD and status updates
- `portAPI.berths` - Berth management and occupancy
- `portAPI.operations` - Operation lifecycle management
- `portAPI.equipment` - Equipment monitoring
- `portAPI.analytics` - KPIs, performance, trends

### Routing

- `/` - Port Dashboard
- `/vessels` - Vessels page (placeholder)
- `/berths` - Berths page (placeholder)
- `/operations` - Operations page (placeholder)
- `/equipment` - Equipment page (placeholder)
- `/analytics` - Analytics page (placeholder)
- `/alerts` - Alerts page (placeholder)
- `/reports` - Reports page (placeholder)
- `/settings` - Settings page (placeholder)

---

## Getting Started

### Prerequisites

- Node.js 18+
- npm or yarn
- Backend API running on `http://localhost:8000`

### Installation

```bash
cd frontend

# Install dependencies
npm install

# Copy environment variables
cp .env.example .env

# Verify .env configuration
cat .env
```

### Environment Configuration

Edit `frontend/.env` if needed:

```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_WS_URL=ws://localhost:8000/ws
VITE_ENV=development
```

### Development Server

```bash
# Start dev server
npm run dev

# Open browser at http://localhost:5173
```

The dashboard will automatically connect to the backend API at `http://localhost:8000/api/v1`.

### Build for Production

```bash
# Type check
npm run type-check

# Build
npm run build

# Preview production build
npm run preview
```

---

## File Structure

```
frontend/src/
├── components/
│   ├── ui/              # Base UI components
│   │   ├── Button.tsx
│   │   ├── Card.tsx
│   │   ├── Badge.tsx
│   │   ├── Input.tsx
│   │   ├── ProgressBar.tsx
│   │   ├── Skeleton.tsx
│   │   └── Tooltip.tsx
│   ├── port/            # SmartPort-specific components
│   │   ├── KPICard.tsx
│   │   ├── BerthCard.tsx
│   │   ├── EquipmentCard.tsx
│   │   └── StatusIndicator.tsx
│   └── layout/          # Layout components
│       ├── Header.tsx
│       ├── Sidebar.tsx
│       └── MainLayout.tsx
├── pages/
│   └── PortDashboard.tsx  # Main dashboard page
├── services/
│   ├── api.ts           # Axios client configuration
│   └── portService.ts   # Port API service layer
├── types/
│   └── port.ts          # TypeScript type definitions
├── lib/
│   └── utils.ts         # Utility functions
├── App.tsx              # React Router setup
├── main.tsx             # App entry point
└── index.css            # Global styles
```

---

## Testing with Backend

### 1. Start Backend API

```bash
cd backend

# Make sure backend is running
uvicorn app.main:app --reload --port 8000
```

### 2. Seed Demo Data

```bash
cd backend

# Load demo data if not already done
python scripts/seed_smartport_demo.py
```

This creates:
- Terminal Santos Grãos organization
- 2 berths (B1 occupied, B2 available)
- 4 vessels with different statuses
- 3 operations (1 in progress at 65%)
- 8 equipment items (including TC2521 with 73% health, 27% failure risk)

### 3. Start Frontend

```bash
cd frontend
npm run dev
```

Visit `http://localhost:5173` and you should see:
- **KPI Cards** with real data from backend
- **Real-time chart** with mock data (will show real data when trends are available)
- **Berth cards** showing B1 (occupied) and B2 (available)
- **Equipment cards** showing critical equipment (TC2521 with high failure risk)

---

## Component Usage Examples

### KPICard

```tsx
<KPICard
  title="Total Throughput"
  value={204490}
  unit="tons"
  format="number"
  icon={<Package className="h-6 w-6" />}
  variant="primary"
  trend={{ value: 8.5, period: 'vs last month' }}
/>
```

### BerthCard

```tsx
<BerthCard
  berth={berthData}
  vesselName="MV GRAIN CARRIER"
  operationProgress={65}
  onClick={() => navigate(`/berths/${berthData.id}`)}
/>
```

### EquipmentCard

```tsx
<EquipmentCard
  equipment={equipmentData}
  onClick={() => navigate(`/equipment/${equipmentData.id}`)}
/>
```

### StatusIndicator

```tsx
<StatusIndicator status={vessel.status} dot size="sm" />
<VesselStatusIndicator status="loading" />
<OperationStatusIndicator status="in_progress" />
<EquipmentStatusIndicator status="operating" />
```

---

## Design System

### Colors

**Status Colors:**
- Success (Green): `#22c55e` - Operating, Available, Loading, Completed
- Warning (Orange): `#f59e0b` - Paused, Anchored, Occupied, Delayed
- Danger (Red): `#ef4444` - Error, Fault, Cancelled, Offline
- Info (Cyan): `#06b6d4` - Scheduled, Planned, Berthed
- Purple: `#8b5cf6` - In Progress, Maintenance

**Background Colors:**
- Dark 900: `#0f172a` - Main background
- Dark 800: `#1e293b` - Cards background
- Dark 700: `#334155` - Borders and dividers

### Typography

- Font Family: Inter (sans-serif)
- Font Mono: JetBrains Mono, Fira Code

### Spacing

Using Tailwind spacing scale (4px base unit):
- `gap-6` - 1.5rem (24px) - Standard grid gap
- `p-6` - 1.5rem (24px) - Card padding
- `rounded-lg` - 0.5rem (8px) - Border radius

---

## API Integration

### Making API Calls

```tsx
import { portAPI } from '@/services/portService';

// Get KPIs
const kpis = await portAPI.analytics.getKPIs(fromDate, toDate);

// List vessels
const vessels = await portAPI.vessels.list({ status: 'loading' });

// Get operation progress
const progress = await portAPI.operations.getProgress(operationId);

// Update vessel status
await portAPI.vessels.updateStatus(vesselId, 'berthed');
```

### Error Handling

API client automatically handles:
- 401 Unauthorized - Redirects to login
- 403 Forbidden - Logs error
- 404 Not Found - Logs error
- 500 Server Error - Logs error
- Network errors - Logs error

Custom error handling:

```tsx
try {
  const data = await portAPI.vessels.list();
  setVessels(data.items);
} catch (error) {
  console.error('Failed to load vessels:', error);
  setError('Failed to load vessels');
}
```

---

## Next Steps (Week 4-8)

### Week 4: Vessels & Operations Management
- Vessel list page with filtering
- Vessel detail page with timeline
- Operation management interface
- Real-time operation monitoring

### Week 5: Equipment & Predictive Maintenance
- Equipment list and detail pages
- Maintenance scheduling interface
- ML predictions integration
- SHAP explanations display

### Week 6: Analytics & Reports
- Advanced analytics dashboard
- Custom report builder
- PDF/Excel export functionality
- Data visualization enhancements

### Week 7-8: Polish & Integration
- WebSocket real-time updates
- Mobile responsive improvements
- Performance optimization
- User authentication
- Testing and bug fixes

---

## Troubleshooting

### Port 5173 already in use

```bash
# Kill process using port 5173
lsof -ti:5173 | xargs kill -9

# Or use different port
npm run dev -- --port 3000
```

### Cannot connect to backend

1. Verify backend is running: `curl http://localhost:8000/api/v1/port/berths`
2. Check `.env` file has correct `VITE_API_BASE_URL`
3. Check browser console for CORS errors
4. Ensure backend allows CORS from frontend origin

### Type errors

```bash
# Run type checker
npm run type-check

# Common fixes:
# - Ensure all imports use '@/' alias
# - Check TypeScript strict mode settings
# - Verify types match backend schemas
```

---

## Resources

- **Tailwind CSS Docs**: https://tailwindcss.com/docs
- **React Router**: https://reactrouter.com/
- **Recharts**: https://recharts.org/
- **Radix UI**: https://www.radix-ui.com/
- **Lucide Icons**: https://lucide.dev/

---

**Frontend MVP Week 3 Complete! 🎉**

All UI components, Port Dashboard, and API integration are ready. The application is now ready for backend integration testing and Week 4 feature development.
