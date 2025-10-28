# 📋 SmartPort Analytics - Testing Checklist

Complete manual testing checklist for validating the Analytics implementation.

---

## ✅ Pre-Testing Setup

- [ ] Backend server running on http://localhost:8000
- [ ] Frontend server running on http://localhost:3000
- [ ] InfluxDB running and accessible
- [ ] PostgreSQL running with user data
- [ ] User account created and can login
- [ ] At least 1 device with tags configured
- [ ] Some time-series data exists in InfluxDB

**Run automated validation:**
```bash
python test_analytics_validation.py
python test_analytics_endpoints.py
```

---

## 🔧 Backend API Tests

### 1. Health Endpoint
- [ ] GET http://localhost:8000/health returns 200
- [ ] Response: `{"status": "healthy"}`

### 2. Analytics Functions Endpoint
- [ ] GET http://localhost:8000/api/v1/analytics/functions returns 200
- [ ] Response contains 13+ aggregation functions
- [ ] Each function has: name, description, category, parameters, example
- [ ] Categories include: Basic, Statistical, Advanced

**Expected functions:**
- [ ] mean, median, mode, min, max, sum, count
- [ ] stddev, variance, percentile
- [ ] correlation, moving_average, cumulative_sum, rate_of_change

### 3. Analytics Examples Endpoint
- [ ] GET http://localhost:8000/api/v1/analytics/examples returns 200
- [ ] Response contains 5+ example queries
- [ ] Each example has: name, description, use_case, query object

**Expected examples:**
- [ ] Production monitoring (P95 latency)
- [ ] Correlation analysis
- [ ] Anomaly detection
- [ ] Trending with moving average
- [ ] Energy consumption analysis

### 4. Analytics Query Endpoint
- [ ] POST http://localhost:8000/api/v1/analytics/query requires authentication (401 without token)
- [ ] With valid token, accepts query and returns results
- [ ] Query validation works (422 for invalid queries)
- [ ] Response includes: query_id, executed_at, execution_time_ms, aggregations, metadata

**Test query:**
```json
{
  "tags": ["your_tag_id"],
  "start": "2024-01-01T00:00:00Z",
  "end": "2024-01-01T23:59:59Z",
  "aggregations": [
    {"function": "mean", "field": "value", "window": "1h"}
  ]
}
```

### 5. API Documentation
- [ ] Swagger UI accessible at http://localhost:8000/docs
- [ ] All analytics endpoints visible in Swagger
- [ ] Can test endpoints directly from Swagger UI
- [ ] ReDoc accessible at http://localhost:8000/redoc
- [ ] OpenAPI spec at http://localhost:8000/openapi.json

---

## 🎨 Frontend Component Tests

### 1. Analytics Page Access
- [ ] Login to SmartPort successfully
- [ ] Analytics page accessible from navigation
- [ ] Page URL: http://localhost:3000/analytics
- [ ] Page loads without errors
- [ ] No console errors in browser DevTools

### 2. Page Layout
- [ ] Header displays "Advanced Analytics"
- [ ] Stats cards show: Available Functions, Example Queries, Query Status
- [ ] "Show Examples" button visible
- [ ] Query Builder component rendered
- [ ] Empty state message visible (before query execution)

### 3. Query Builder - TagSelector Component
- [ ] Component renders with "Select tags..." placeholder
- [ ] Search input functional
- [ ] Dropdown opens on focus
- [ ] Can select tags from dropdown
- [ ] Selected tags appear as chips
- [ ] Can remove selected tags (X button)
- [ ] Shows device name and unit for each tag
- [ ] Maximum 10 tags enforced
- [ ] Tag search filters results in real-time

### 4. Query Builder - TimeRangePicker Component
- [ ] 6 preset buttons visible: 1h, 6h, 24h, 7d, 30d, Custom
- [ ] Can select preset (button highlights)
- [ ] Time range updates when preset selected
- [ ] Custom option shows datetime-local inputs
- [ ] Can manually enter start/end times
- [ ] Duration summary displays (X hours/days)
- [ ] Validates start < end

### 5. Query Builder - FilterBuilder Component
- [ ] "Add Filter" button visible
- [ ] Can add multiple filters
- [ ] Each filter has: field, operator, value input(s)
- [ ] Field options: value, quality, tag_id
- [ ] Operator options: =, ≠, >, <, ≥, ≤, in, between
- [ ] Value input adapts to operator:
  - [ ] Single input for =, ≠, >, <, ≥, ≤
  - [ ] Comma-separated for "in"
  - [ ] Two inputs for "between"
- [ ] Can remove filters (trash icon)

### 6. Query Builder - AggregationBuilder Component
- [ ] "Add Aggregation" button visible
- [ ] Can add multiple aggregations
- [ ] Each aggregation has: function, field, window, params
- [ ] Function dropdown grouped by category:
  - [ ] Basic: mean, median, mode, min, max, sum, count
  - [ ] Statistical: stddev, variance, percentile
  - [ ] Advanced: correlation, moving_average, etc.
- [ ] Field options: value, quality
- [ ] Window options: 1m, 5m, 15m, 30m, 1h, 6h, 1d
- [ ] Function-specific parameters show:
  - [ ] Percentile: 0-100 input
  - [ ] Correlation: target tag input
  - [ ] Moving average: type + window size
- [ ] Can remove aggregations (trash icon)

### 7. Query Builder - Main Component
- [ ] Header shows "Query Builder"
- [ ] Mode toggle visible (if streaming enabled):
  - [ ] "Execute Once" button
  - [ ] "Stream Live" button
- [ ] "Show/Hide JSON" button works
- [ ] JSON preview shows correctly formatted query
- [ ] "Include raw data" checkbox functional
- [ ] Action buttons visible:
  - [ ] Save Query
  - [ ] Export (downloads JSON file)
  - [ ] Execute Query (blue, disabled if invalid)
- [ ] Query Summary displays:
  - [ ] N tag(s) selected
  - [ ] Time range: preset/custom (X hours)
  - [ ] N filter(s) applied
  - [ ] N aggregation(s) configured
- [ ] Validation messages show for invalid queries

### 8. Execute Once Mode
- [ ] Execute button triggers query
- [ ] Loading spinner shows during execution
- [ ] Button disabled while loading
- [ ] Results appear after execution
- [ ] Error message displays if query fails

### 9. Stream Live Mode
- [ ] Toggle to "Stream Live" mode
- [ ] StreamControls component appears
- [ ] Execute Query button hidden
- [ ] Stream controls show:
  - [ ] Connection status (WiFi icon: green/gray)
  - [ ] Refresh interval picker (7 options)
  - [ ] Start Stream button (green)
- [ ] Clicking Start Stream:
  - [ ] Connects to WebSocket
  - [ ] Status changes to "Connected"
  - [ ] Start button becomes Pause/Stop
  - [ ] Streaming indicator shows (red pulsing radio icon)
  - [ ] Sequence counter increments (#0001, #0002...)
  - [ ] Last update timestamp shows
- [ ] Pause button:
  - [ ] Pauses streaming (yellow icon)
  - [ ] Keeps connection open
  - [ ] Changes to Resume button
- [ ] Resume button:
  - [ ] Resumes streaming
  - [ ] Icon changes back to red pulsing
- [ ] Stop button:
  - [ ] Stops streaming
  - [ ] Closes WebSocket connection
  - [ ] Returns to initial state
- [ ] Refresh interval picker:
  - [ ] Shows current interval
  - [ ] Dropdown with 7 options (1s, 2s, 5s, 10s, 30s, 1m, 5m)
  - [ ] Can change interval before streaming
  - [ ] Disabled during active stream
- [ ] Error handling:
  - [ ] Connection errors show red banner
  - [ ] Auto-reconnect attempts after 3s
  - [ ] Error message details displayed

---

## 📊 Visualization Tests

### 1. Results Display
- [ ] Results section appears after query execution
- [ ] Results header shows:
  - [ ] "Query Results" title
  - [ ] Execution time in ms
  - [ ] Total records count
  - [ ] Export CSV button
- [ ] Aggregation summary cards show:
  - [ ] Function name
  - [ ] Mean/result value
  - [ ] Data point count
- [ ] Visualization type selector visible
- [ ] Auto-select works based on data

### 2. Auto-Select Visualization
- [ ] Time series data → MultiAxisChart
- [ ] Few data points (≤10) → BarChart
- [ ] Appropriate chart renders automatically

### 3. Manual Visualization Selection
- [ ] Dropdown shows: Auto-Select, Time Series, Bar, Scatter, Heatmap, Box
- [ ] Can manually select visualization type
- [ ] Chart re-renders with selected type
- [ ] Chart data updates correctly

### 4. MultiAxisChart Component
- [ ] Renders for time-series data
- [ ] X-axis shows timestamps
- [ ] Y-axis shows values
- [ ] Multiple series supported
- [ ] Different Y-axes for different units
- [ ] Legend shows series names
- [ ] Hover shows data point details
- [ ] Zoom and pan work
- [ ] Responsive to window resize

### 5. BarChart Component
- [ ] Renders for categorical data
- [ ] X-axis shows categories
- [ ] Y-axis shows values
- [ ] Multiple series stack or group
- [ ] Colors distinguish series
- [ ] Hover shows exact values
- [ ] Legend toggles series visibility

### 6. Other Visualization Components
Test each of the 12 components individually (see Visualization Components Checklist below)

### 7. Export CSV
- [ ] Export CSV button works
- [ ] Downloads file: analytics-results-[timestamp].csv
- [ ] CSV contains correct data
- [ ] Headers: timestamp, tag_id, value
- [ ] Data matches query results

### 8. Raw Data Table
- [ ] Table appears if include_raw_data enabled
- [ ] Shows first 100 rows
- [ ] Columns: Timestamp, Tag ID, Value, Quality
- [ ] Timestamps formatted correctly
- [ ] Quality badges color-coded (green=good, yellow=uncertain)
- [ ] Table scrollable horizontally and vertically

---

## 🎨 Individual Visualization Components

Create a test page with sample data for each component:

### 1. GaugeChart
- [ ] Renders circular gauge
- [ ] Shows current value
- [ ] Min/max range correct
- [ ] Thresholds color-coded (green/yellow/red)
- [ ] Delta shows change from previous
- [ ] Unit displays correctly
- [ ] Responsive to container size

### 2. HeatmapChart
- [ ] Renders 2D color matrix
- [ ] Color scale shows intensity
- [ ] Hover shows exact value
- [ ] Row/column labels visible
- [ ] Color legend displayed
- [ ] Supports correlation matrices

### 3. ScatterPlot
- [ ] Renders X vs Y plot
- [ ] Points color-coded by series
- [ ] Trendline optional and working
- [ ] Hover shows point details
- [ ] Supports multiple series
- [ ] Zoom and pan work

### 4. MultiAxisChart
- [ ] Multiple Y-axes (left/right)
- [ ] Different units on each axis
- [ ] Line styles: solid, dash, dot
- [ ] Legend shows all series
- [ ] Colors distinguish series

### 5. BarChart
- [ ] Vertical bars
- [ ] Grouped or stacked mode
- [ ] Horizontal option works
- [ ] Colors configurable
- [ ] Hover shows values

### 6. PieChart
- [ ] Circular pie chart
- [ ] Donut mode optional
- [ ] Percentages shown
- [ ] Labels on slices
- [ ] Hover shows details
- [ ] Exploded slices optional

### 7. BoxPlot
- [ ] Shows quartiles (Q1, median, Q3)
- [ ] Whiskers extend to min/max
- [ ] Outliers plotted separately
- [ ] Multiple groups supported
- [ ] Hover shows statistics

### 8. WaterfallChart
- [ ] Shows sequential changes
- [ ] Initial value at start
- [ ] Increases in green/blue
- [ ] Decreases in red
- [ ] Total at end
- [ ] Connecting lines visible
- [ ] Labels on bars

### 9. RadarChart
- [ ] Circular/polygon shape
- [ ] Multiple axes radiating from center
- [ ] Multiple series overlay
- [ ] Area fill option
- [ ] Axis labels visible
- [ ] Hover shows values

### 10. SankeyDiagram
- [ ] Shows flow between nodes
- [ ] Flow width proportional to value
- [ ] Node labels visible
- [ ] Hover shows flow details
- [ ] Colors distinguish flows
- [ ] Interactive (drag nodes?)

### 11. TreemapChart
- [ ] Rectangular tiles
- [ ] Tile size proportional to value
- [ ] Hierarchical nesting
- [ ] Colors distinguish categories
- [ ] Labels on tiles
- [ ] Hover shows exact value
- [ ] Click to zoom into category

### 12. GeoMap
- [ ] Map displays (OpenStreetMap)
- [ ] Markers at lat/lon coordinates
- [ ] Marker colors by status (green/yellow/red)
- [ ] Hover shows site details
- [ ] Zoom and pan work
- [ ] Multiple markers supported
- [ ] Custom icons optional

---

## 🔌 WebSocket Streaming Tests

### 1. Connection Management
- [ ] WebSocket connects successfully
- [ ] JWT token passed via query param
- [ ] Connection status updates in UI
- [ ] Can disconnect manually
- [ ] Auto-reconnect after disconnect (3s)

### 2. Streaming Lifecycle
- [ ] Start streaming sends correct message
- [ ] Server responds with status acknowledgment
- [ ] Data updates arrive at refresh interval
- [ ] Sequence numbers increment correctly
- [ ] Timestamps update with each message

### 3. Real-time Data Updates
- [ ] Visualizations update with new data
- [ ] Charts animate smoothly (no flickering)
- [ ] Old data clears or appends correctly
- [ ] Multiple series update together
- [ ] No memory leaks (check DevTools Memory)

### 4. Stream Controls
- [ ] Pause preserves connection
- [ ] Resume continues from where paused
- [ ] Stop closes connection cleanly
- [ ] Change refresh interval works
- [ ] Update query without restarting

### 5. Error Handling
- [ ] Network errors show in UI
- [ ] WebSocket close handled gracefully
- [ ] Invalid query shows error
- [ ] Rate limiting respected (50/min)
- [ ] Connection errors trigger reconnect

### 6. Performance
- [ ] Streams at 1s interval without lag
- [ ] No UI freezing during streaming
- [ ] Multiple tabs can stream independently
- [ ] Memory usage stable over time (use Performance Monitor)
- [ ] CPU usage reasonable (<30%)

---

## 🚀 Integration Tests

### 1. Full Query Workflow
- [ ] Select 3 tags
- [ ] Set time range to "Last 24 Hours"
- [ ] Add filter: value > 100
- [ ] Add aggregation: mean with 1h window
- [ ] Execute query
- [ ] Results display correctly
- [ ] Export CSV works
- [ ] Visualization shows data

### 2. Streaming Workflow
- [ ] Select 2 tags
- [ ] Set time range to "Last 1 Hour"
- [ ] Add aggregation: mean with 5m window
- [ ] Toggle to Stream Live mode
- [ ] Set refresh interval to 5s
- [ ] Start streaming
- [ ] Watch 5 updates arrive
- [ ] Pause stream
- [ ] Resume stream
- [ ] Stop stream

### 3. Save/Load Query
- [ ] Build complex query
- [ ] Click "Save Query"
- [ ] Enter name "Test Query 1"
- [ ] Query saved to localStorage
- [ ] Reload page
- [ ] Load saved query
- [ ] Query parameters restored
- [ ] Execute loaded query

### 4. Example Queries
- [ ] Click "Show Examples"
- [ ] Click on example query
- [ ] Example executes automatically
- [ ] Results display
- [ ] Can modify example query
- [ ] Re-execute modified query

### 5. Multi-Aggregation Query
- [ ] Select 1 tag
- [ ] Add 3 aggregations: mean, min, max
- [ ] Execute query
- [ ] 3 aggregation results returned
- [ ] All 3 show in summary cards
- [ ] Visualization shows all 3 series

### 6. Cross-Tag Analysis
- [ ] Select 5 different tags
- [ ] Add correlation aggregation
- [ ] Execute query
- [ ] Correlation matrix returned
- [ ] Heatmap visualization auto-selected
- [ ] Can see correlations between all tags

---

## 🐛 Error Handling Tests

### 1. Invalid Queries
- [ ] No tags selected → validation error message
- [ ] No aggregations → validation error message
- [ ] Start time after end time → validation error
- [ ] Invalid tag ID → backend error handled
- [ ] Empty results → "No data found" message

### 2. Network Errors
- [ ] Stop backend during query → error displayed
- [ ] Timeout after 30s → error message
- [ ] Stop backend during streaming → reconnect attempted
- [ ] Rate limit exceeded → appropriate error

### 3. Authentication Errors
- [ ] Invalid token → 401 redirect to login
- [ ] Expired token → 401 redirect to login
- [ ] No token → 401 redirect to login

### 4. Data Validation
- [ ] Invalid percentile (>100) → validation error
- [ ] Invalid time window → validation error
- [ ] Invalid operator → validation error
- [ ] Malformed JSON export → error handled

---

## 📱 Responsive Design Tests

### 1. Desktop (1920x1080)
- [ ] All components visible
- [ ] No horizontal scroll
- [ ] Query Builder fits in viewport
- [ ] Visualizations full width
- [ ] Controls accessible

### 2. Laptop (1366x768)
- [ ] Layout adapts
- [ ] Components stack appropriately
- [ ] Text readable
- [ ] No overlapping elements

### 3. Tablet (768x1024)
- [ ] Mobile layout activates
- [ ] Touch-friendly controls
- [ ] Dropdowns accessible
- [ ] Charts resize correctly

### 4. Mobile (375x667)
- [ ] Single column layout
- [ ] Components stack vertically
- [ ] Text size readable
- [ ] Buttons thumb-sized
- [ ] No horizontal scroll

---

## 🎯 Performance Tests

### 1. Query Performance
- [ ] Simple query (1 tag, 1h) < 500ms
- [ ] Complex query (10 tags, 24h) < 3s
- [ ] Large dataset (10k points) < 5s
- [ ] Concurrent queries work

### 2. Rendering Performance
- [ ] Chart renders < 100ms
- [ ] 1000 data points smooth
- [ ] Animation smooth (60fps)
- [ ] No jank when interacting

### 3. Memory Usage
- [ ] Initial page load < 50MB
- [ ] After 10 queries < 100MB
- [ ] No memory leaks (check heap snapshots)
- [ ] Streaming for 5 mins stable

### 4. Network Usage
- [ ] Query response < 1MB
- [ ] WebSocket messages < 10KB each
- [ ] No unnecessary requests
- [ ] Assets cached correctly

---

## ✅ Browser Compatibility

Test on:
- [ ] Chrome/Chromium (latest)
- [ ] Firefox (latest)
- [ ] Safari (latest) - Mac only
- [ ] Edge (latest)
- [ ] Mobile Safari - iOS
- [ ] Mobile Chrome - Android

Check:
- [ ] All features work
- [ ] No console errors
- [ ] UI renders correctly
- [ ] WebSocket works
- [ ] Charts display properly

---

## 📝 Final Checklist

- [ ] All automated tests pass
- [ ] All manual tests pass
- [ ] No console errors
- [ ] No network errors
- [ ] Documentation updated
- [ ] Known issues documented
- [ ] Performance acceptable
- [ ] Ready for demo

---

## 🎉 Sign-Off

When all tests pass:

**Tested by:** _______________
**Date:** _______________
**Version:** v1.0.0-analytics
**Status:** ✅ READY FOR DEMO

**Notes:**
- [ ] Minor issues: _______________
- [ ] Blockers: _______________
- [ ] Recommendations: _______________

---

**Next Step:** Create demo/showcase page (Option 2)
