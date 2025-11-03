# OptiFlow AI - User Manual: Advanced Features

## Table of Contents

1. [Introduction](#introduction)
2. [Getting Started](#getting-started)
3. [Gateway Production Tools](#gateway-production-tools)
4. [ML Failure Prediction](#ml-failure-prediction)
5. [Loading Optimization](#loading-optimization)
6. [Report Generation](#report-generation)
7. [Mobile Access](#mobile-access)
8. [Troubleshooting](#troubleshooting)
9. [FAQ](#faq)

---

## Introduction

Welcome to OptiFlow AI Advanced Features! This manual will guide you through using the five advanced production features:

- **Gateway Production Tools** - Test and validate industrial gateways before deployment
- **ML Failure Prediction** - Predict equipment failures using machine learning
- **Loading Optimization** - Optimize ship loading operations for maximum efficiency
- **Report Generation** - Generate professional PDF and Excel reports
- **Mobile Access** - Access critical information on mobile devices

### Who Should Use This Manual?

- **Operations Managers** - Monitor and optimize operations
- **Maintenance Teams** - Predict and prevent equipment failures
- **IT/OT Engineers** - Configure and test industrial gateways
- **Field Operators** - Access real-time information on mobile devices
- **Executives** - Review operational reports and metrics

---

## Getting Started

### System Requirements

- **Web Browser:** Chrome, Firefox, Safari, or Edge (latest version)
- **Mobile:** iOS 12+ or Android 8+
- **Network:** Stable internet connection
- **Permissions:** User account with appropriate access level

### Logging In

1. Navigate to OptiFlow AI URL: `https://your-domain.com`
2. Enter your username and password
3. Click "Login"
4. Navigate to "Advanced Features" section in the main menu

---

## Gateway Production Tools

Use these tools to test and validate industrial gateway configurations before deploying to production.

### When to Use Gateway Production Tools

✅ **Use when:**
- Setting up a new industrial gateway
- Modifying existing gateway configuration
- Troubleshooting connection issues
- Planning capacity for new equipment
- Validating vendor-provided configurations

❌ **Don't use when:**
- The gateway is already in production (use monitoring instead)
- You don't have network access to the target device

---

### Testing a Gateway Connection

**Purpose:** Verify that a gateway can connect to an industrial device and measure performance.

#### Step-by-Step:

1. **Navigate** to Advanced Features → Gateway Production Tools → Test Connection

2. **Fill in Gateway Details:**
   - **Name:** Descriptive name (e.g., "Silo 3 PLC Gateway")
   - **Protocol:** Select from dropdown (OPC-UA, Modbus TCP, Siemens S7, Rockwell)
   - **Host:** IP address of the device (e.g., 192.168.1.100)
   - **Port:** Protocol port (default values pre-filled)

3. **Add Tags** (optional but recommended):
   - Click "Add Tag"
   - Enter tag name, address/node ID, and data type
   - Add multiple tags to test multiple data points

4. **Click "Test Connection"**

5. **Review Results:**
   - ✅ **Connection Successful:** Green indicator
   - ⚠️ **Connection Failed:** Red indicator with error message
   - **Performance Metrics:**
     - Connection time
     - Average read time
     - Reads per second
     - Success rate
   - **Reliability Test:**
     - Reconnection successful
     - Reconnection time

#### Example:

```
Gateway Name: Production Line 1 PLC
Protocol: Modbus TCP
Host: 192.168.1.150
Port: 502

Tags:
- Temperature (address: 40001, type: FLOAT)
- Pressure (address: 40002, type: FLOAT)

Results:
✅ Connection Successful
   Connection time: 125 ms
   Average read time: 42 ms
   Reads per second: 23
   Success rate: 100%
```

---

### Validating Gateway Configuration

**Purpose:** Check if your gateway configuration follows best practices.

#### Step-by-Step:

1. **Navigate** to Advanced Features → Gateway Production Tools → Validate Configuration

2. **Upload or Paste Configuration:**
   - Upload JSON file, or
   - Paste configuration manually

3. **Click "Validate"**

4. **Review Validation Results:**
   - ✅ **Valid:** Configuration is correct
   - ❌ **Errors:** Critical issues that must be fixed
   - ⚠️ **Warnings:** Recommendations for improvement

#### Common Warnings:

- **"Security not enabled"** - Enable authentication for production
- **"No timeout configured"** - Add connection timeout
- **"Duplicate tag names"** - Each tag must have unique name
- **"High scan rate"** - May overload network or device

---

### Getting Production Templates

**Purpose:** Start with a proven, production-ready configuration template.

#### Step-by-Step:

1. **Navigate** to Advanced Features → Gateway Production Tools → Templates

2. **Select Gateway Type:**
   - OPC-UA
   - Modbus TCP
   - Siemens S7
   - Rockwell

3. **Click "Generate Template"**

4. **Download Template:**
   - Click "Download JSON"
   - Template includes security settings, timeouts, retry policies, and sample tags

5. **Customize Template:**
   - Update host, port, and tags for your environment
   - Keep security and reliability settings unchanged

---

## ML Failure Prediction

Predict equipment failures before they happen using machine learning.

### How It Works

The ML system analyzes 8 key factors:
1. Health Score (0-100)
2. Alarm Severity
3. Operating Hours vs Expected Life
4. Vibration Levels
5. Temperature
6. Load Percentage
7. Days Since Last Maintenance
8. Recent Alarm Count

Based on these factors, it predicts the probability of failure within the next 24 hours (or custom time horizon).

---

### Training the ML Model

**Important:** Train the model before using predictions. Retrain monthly for best accuracy.

#### Step-by-Step:

1. **Navigate** to Advanced Features → ML Prediction → Train Model

2. **Configure Training:**
   - **Asset Type** (optional): Train for specific type (conveyor, silo, loader, etc.)
   - **Training Days:** 30-365 days (default: 180)
     - More days = more data = better accuracy
     - But very old data may not reflect current conditions

3. **Click "Train Model"**

4. **Wait for Training:**
   - Progress bar shows completion
   - Typically takes 2-5 minutes depending on data volume

5. **Review Results:**
   - **Train Accuracy:** How well model learned from training data
   - **Test Accuracy:** How well model predicts new data
   - **Target:** 80%+ test accuracy
   - If < 70%, consider more training days or check data quality

#### Example:

```
Training Configuration:
  Asset Type: Conveyor
  Training Days: 180

Results:
  ✅ Training Complete
  Train Accuracy: 92%
  Test Accuracy: 88%
  Training Samples: 1,250
  Model File: conveyor_20240105.pkl
```

---

### Predicting Equipment Failures

**Purpose:** Identify which equipment is at risk of failure.

#### Step-by-Step:

1. **Navigate** to Advanced Features → ML Prediction → Predict Failure

2. **Select Asset:**
   - Search by asset ID or name
   - Or browse asset list

3. **Set Prediction Horizon:**
   - Default: 24 hours
   - Range: 1-168 hours (1 week)
   - Shorter horizons = more accurate

4. **Click "Predict"**

5. **Interpret Results:**

   **Risk Levels:**
   - 🔴 **Critical (≥80%):** Immediate action required
   - 🟠 **High (≥60%):** Schedule maintenance within 24 hours
   - 🟡 **Medium (≥40%):** Monitor closely, plan maintenance
   - 🟢 **Low (<40%):** Continue normal operations

6. **Follow Recommendations:**
   - System provides specific action items
   - Examples:
     - "Schedule maintenance within next 12 hours"
     - "Reduce operating load by 30%"
     - "Monitor vibration levels closely"
     - "Prepare replacement parts"

#### Example Prediction:

```
Asset: CONV-001 (Conveyor Belt 1)
Prediction Horizon: 24 hours

Results:
  Failure Probability: 72%
  Risk Level: 🟠 HIGH
  Estimated Time to Failure: 18 hours
  Confidence: 88%

Recommendations:
  1. Schedule maintenance within next 24 hours
  2. Reduce operating load by 30%
  3. Monitor vibration levels closely
  4. Prepare replacement parts

Contributing Factors:
  - High vibration: 35%
  - Low health score: 25%
  - Overdue maintenance: 20%
  - Recent alarms: 15%
  - High load: 5%
```

---

### Best Practices for ML Predictions

✅ **Do:**
- Train model monthly with fresh data
- Act on high/critical predictions immediately
- Track prediction accuracy vs actual failures
- Use predictions to plan preventive maintenance
- Combine predictions with operator knowledge

❌ **Don't:**
- Ignore critical predictions
- Over-rely on predictions for low-risk assets
- Use predictions without context
- Skip model retraining for >3 months

---

## Loading Optimization

Optimize ship loading operations to minimize waiting time and maximize throughput.

### Berth Allocation Optimization

**Purpose:** Allocate ships to berths to minimize total waiting time.

#### Step-by-Step:

1. **Navigate** to Advanced Features → Loading Optimization → Berth Allocation

2. **Select Site and Time Period:**
   - Choose your site from dropdown
   - Set "Days Ahead" (1-30, default: 7)

3. **Click "Optimize"**

4. **Review Allocation Plan:**
   - Table shows each ship with:
     - Ship name
     - Allocated berth
     - Scheduled arrival
     - Allocated start time
     - Estimated duration
     - Waiting hours
   - **Summary Metrics:**
     - Total waiting hours
     - Berth utilization %

5. **Export or Implement:**
   - Click "Export to Excel" to share with team
   - Click "Apply to Schedule" to update system

#### Example:

```
Site: Santos Terminal
Period: Next 7 days
Ships Scheduled: 5

Optimized Allocation:
  MV Atlantic → Berth 1 (arrives 8am, starts 8am, 0h wait)
  MV Pacific → Berth 1 (arrives 12pm, starts 2pm next day, 26h wait)
  MV Baltic → Berth 2 (arrives 2pm, starts 2pm, 0h wait)

Summary:
  Total Waiting: 26 hours
  Berth Utilization: 78.5%

vs Manual Allocation:
  Total Waiting: 54 hours (-52% improvement)
  Berth Utilization: 65.2%
```

---

### Loading Sequence Optimization

**Purpose:** Determine optimal order and silos for loading a ship.

#### Step-by-Step:

1. **Navigate** to Advanced Features → Loading Optimization → Loading Sequence

2. **Select Ship:**
   - Choose ship from current loadings
   - Or search by ship name/IMO

3. **Click "Optimize Sequence"**

4. **Review Loading Plan:**
   - Sequence of silos to use
   - Tonnage from each silo
   - Estimated time for each phase
   - Total loading time
   - Timeline (start and end times)

5. **Share with Operations:**
   - Print loading plan
   - Send to mobile devices
   - Update whiteboard/displays

#### Example:

```
Ship: MV Atlantic
Product: Soybean
Total Tonnage: 50,000 tons

Optimized Sequence:
  1. Silo 3 → 8,000 tons @ 1,200 t/h (6.7 hours)
  2. Silo 1 → 10,000 tons @ 1,100 t/h (9.1 hours)
  3. Silo 5 → 12,000 tons @ 1,150 t/h (10.4 hours)
  4. Silo 2 → 20,000 tons @ 1,000 t/h (20.0 hours)

Total Time: 42.5 hours
Completion: Jan 7, 2:30 AM
```

---

### Optimal Loading Rate

**Purpose:** Calculate safe loading rate based on weather conditions.

#### Step-by-Step:

1. **Navigate** to Advanced Features → Loading Optimization → Loading Rate

2. **Select Ship:**
   - Choose active ship loading

3. **Enter Weather Conditions:**
   - Wind speed (km/h)
   - Rainfall (mm)
   - Temperature (°C)
   - System may auto-fill from weather station

4. **Click "Calculate Optimal Rate"**

5. **Review Recommendations:**
   - Base rate
   - Optimal rate (adjusted)
   - Reduction percentage
   - Limiting factors
   - Safety recommendations

#### Weather Impact:

| Condition | Adjustment |
|-----------|------------|
| Wind > 60 km/h | -50% (consider stopping) |
| Wind 40-60 km/h | -30% |
| Rainfall > 5mm | -20% |
| Good conditions | No adjustment |

#### Example:

```
Ship: MV Atlantic
Base Rate: 1,200 t/h

Current Weather:
  Wind: 45 km/h
  Rainfall: 2 mm
  Temperature: 25°C

Optimal Rate: 840 t/h (-30%)

Adjustments:
  - Wind 45 km/h: -30% reduction
  - Rainfall OK (< 5mm threshold)

Recommendations:
  ✅ Safe to load at reduced rate
  ⚠️ Monitor wind continuously
  ⚠️ Prepare to pause if wind > 60 km/h
```

---

## Report Generation

Generate professional reports for operations, compliance, and management.

### Daily Operations PDF Report

**Purpose:** Summary of daily operations in professional PDF format.

#### Step-by-Step:

1. **Navigate** to Advanced Features → Reports → Daily PDF

2. **Select Parameters:**
   - Site
   - Operation Date

3. **Click "Generate PDF"**

4. **Wait for Generation:**
   - Progress indicator
   - Typically takes 5-10 seconds

5. **Download and Review:**
   - PDF opens automatically
   - Or download from link

#### Report Contents:

**Page 1: Summary**
- Site name and date
- Total trucks processed
- Total tonnage received
- Ships loaded/loading
- Key metrics

**Page 2: Truck Details**
- Table of all truck entries
- License plate, driver, product type
- Weights (gross, tare, net)
- Entry and exit times

**Page 3: Ship Details**
- All ship loadings for the day
- Ship name, IMO, product type
- Tonnage (estimated and actual)
- Loading progress and status

---

### Operations Excel Report

**Purpose:** Detailed multi-day operations data for analysis.

#### Step-by-Step:

1. **Navigate** to Advanced Features → Reports → Operations Excel

2. **Select Parameters:**
   - Site
   - Start Date
   - End Date (up to 30 days range)

3. **Click "Generate Excel"**

4. **Wait for Generation:**
   - Progress indicator
   - May take 30-60 seconds for large date ranges

5. **Download Excel File:**
   - Click download link
   - Open in Excel, Google Sheets, or similar

#### Excel Sheets:

**Sheet 1: Summary**
- Daily totals by date
- Trends and comparisons
- Charts (if enabled)

**Sheet 2: Caminhões (Trucks)**
- Detailed truck entry records
- All fields with filters
- Sortable columns

**Sheet 3: Navios (Ships)**
- Detailed ship loading records
- Status, progress, tonnage
- Sortable and filterable

#### Use Cases:

- Monthly reports for management
- Compliance and audit documentation
- Performance analysis
- Billing and invoicing
- Historical trend analysis

---

## Mobile Access

Access critical information on mobile devices for field operations.

### Mobile Dashboard

**Purpose:** Quick overview of site operations on mobile.

#### Accessing:

1. Open mobile browser
2. Navigate to OptiFlow AI URL
3. Login with credentials
4. Tap "Mobile View" or navigate to `/mobile`

#### Dashboard Shows:

**Trucks:**
- Currently active: 12
- Completed today: 45
- Total tonnage: 1,350 tons

**Ships:**
- Loading now: 2
- Scheduled: 3
- Completed today: 0

**Alerts:**
- Critical: 1
- Warnings: 3

**Weather:**
- Wind speed
- Rainfall
- Loading status (good/caution/stop)

---

### Mobile Ship Status

**Purpose:** Real-time ship loading progress for field operators.

#### Step-by-Step:

1. **Open Mobile Dashboard**

2. **Tap on Ship:**
   - Select from "Loading Now" list
   - Or search by ship name

3. **View Real-Time Status:**
   - Loading progress (%)
   - Tonnage loaded / remaining
   - Current loading rate
   - ETA to completion
   - Current silo being used
   - Any alerts or issues

4. **Refresh:**
   - Pull down to refresh
   - Auto-refreshes every 60 seconds

#### Example Mobile View:

```
🚢 MV Atlantic
Status: Loading (65%)

Progress:
█████████░░░░░░ 65%

Loaded: 32,500 tons
Remaining: 17,500 tons

Current Rate: 1,050 t/h
ETA: Jan 6, 2:30 PM
Hours Remaining: 16.5

Current: Silo 2
Next: Silo 5

Alerts: None
```

---

## Troubleshooting

### Gateway Connection Test Fails

**Problem:** Cannot connect to gateway

**Solutions:**
1. **Check network connectivity:**
   - Ping the IP address
   - Verify firewall rules
   - Ensure VPN is connected (if required)

2. **Verify credentials:**
   - Username and password correct
   - Certificate valid (for OPC-UA)

3. **Check device status:**
   - Is the PLC/device powered on?
   - Is it responding to other connections?

4. **Review port and protocol:**
   - Correct port number?
   - Protocol matches device?

---

### ML Prediction Shows "Model Not Found"

**Problem:** Cannot make predictions

**Solution:**
1. Navigate to ML Prediction → Train Model
2. Train model with at least 30 days of data
3. Wait for training to complete
4. Try prediction again

---

### Report Generation Takes Too Long

**Problem:** Report doesn't generate or times out

**Solutions:**
1. **Reduce date range:**
   - Use shorter periods (7 days instead of 30)
   - Generate multiple smaller reports

2. **Check data volume:**
   - Very high traffic days may take longer
   - Be patient for first-time generation

3. **Try different time:**
   - Avoid peak usage hours
   - Generate reports during off-hours

---

### Mobile View Not Loading

**Problem:** Mobile dashboard shows errors

**Solutions:**
1. **Check mobile connection:**
   - Switch to WiFi if on cellular
   - Verify internet connectivity

2. **Clear browser cache:**
   - Settings → Clear browsing data
   - Reload page

3. **Try different browser:**
   - Use Chrome, Safari, or Firefox
   - Update browser to latest version

---

## FAQ

### Q: How often should I train the ML model?

**A:** Train monthly for best accuracy. If you notice declining prediction quality, retrain sooner.

---

### Q: Can I test a gateway that's already in production?

**A:** Use the benchmark feature instead of full connection test to avoid disrupting operations.

---

### Q: What's the difference between PDF and Excel reports?

**A:**
- **PDF:** Professional format for sharing, printing, archiving. Fixed layout.
- **Excel:** For analysis, sorting, filtering, charts. Editable.

---

### Q: Can multiple ships use the same berth?

**A:** Yes, the optimizer allocates ships sequentially to the same berth, minimizing gaps and waiting time.

---

### Q: How accurate are the ML predictions?

**A:** With proper training (180+ days), accuracy is typically 85-90%. Always combine with operator judgment.

---

### Q: Can I customize report templates?

**A:** Not directly in the UI. Contact your system administrator for custom report templates.

---

### Q: Does the mobile view work offline?

**A:** No, requires internet connection. However, pages cache briefly for quick reloading.

---

### Q: What happens if weather exceeds safe loading limits?

**A:** The system will recommend stopping operations. Final decision rests with operations manager.

---

## Getting Help

**Technical Support:**
- Email: support@optiflow.ai
- Phone: +1 (555) 123-4567
- Hours: 24/7

**Documentation:**
- User Manual: https://docs.optiflow.ai/user-manual
- API Docs: https://docs.optiflow.ai/api
- Video Tutorials: https://docs.optiflow.ai/videos

**Training:**
- Contact your account manager for on-site training
- Webinars: First Tuesday of each month
- Self-paced courses: https://learn.optiflow.ai

---

**Version:** 1.0
**Last Updated:** January 2024
**© 2024 OptiFlow AI. All rights reserved.**
