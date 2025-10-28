// SmartPort Soak Test (Endurance Test)
// Tests system stability over extended period
// Run with: k6 run soak-test.js

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';

const errorRate = new Rate('errors');
const memoryTrend = new Trend('memory_usage');

// Soak test configuration: Moderate load for long duration
export const options = {
  stages: [
    { duration: '5m', target: 30 },   // Ramp up to 30 users
    { duration: '60m', target: 30 },  // Stay at 30 users for 1 hour
    { duration: '5m', target: 0 },    // Ramp down
  ],
  thresholds: {
    'http_req_duration': ['p(95)<500', 'p(99)<1000'], // Consistent performance
    'http_req_failed': ['rate<0.01'],   // Less than 1% errors
    'errors': ['rate<0.01'],
  },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';
const API_PREFIX = '/api/v1';

export function setup() {
  const loginRes = http.post(`${BASE_URL}${API_PREFIX}/auth/login`, {
    username: 'testuser',
    password: 'testpass123',
  });

  console.log('Starting soak test - will run for approximately 70 minutes');
  return { token: loginRes.json('access_token') };
}

export default function (data) {
  const headers = {
    'Authorization': `Bearer ${data.token}`,
    'Content-Type': 'application/json',
  };

  // Simulate realistic user behavior
  // 1. Check organizations
  let res = http.get(`${BASE_URL}${API_PREFIX}/organizations/`, { headers });
  check(res, {
    'list organizations OK': (r) => r.status === 200,
  }) || errorRate.add(1);
  sleep(2);

  // 2. Check sites
  res = http.get(`${BASE_URL}${API_PREFIX}/sites/`, { headers });
  check(res, {
    'list sites OK': (r) => r.status === 200,
  }) || errorRate.add(1);
  sleep(2);

  // 3. Check devices
  res = http.get(`${BASE_URL}${API_PREFIX}/devices/`, { headers });
  check(res, {
    'list devices OK': (r) => r.status === 200,
  }) || errorRate.add(1);
  sleep(2);

  // 4. Check tags
  res = http.get(`${BASE_URL}${API_PREFIX}/tags/`, { headers });
  check(res, {
    'list tags OK': (r) => r.status === 200,
  }) || errorRate.add(1);
  sleep(2);

  // 5. Health check
  res = http.get(`${BASE_URL}/health`);
  check(res, {
    'health check OK': (r) => r.status === 200,
  }) || errorRate.add(1);

  // Longer sleep to simulate user thinking time
  sleep(5);
}

export function teardown(data) {
  console.log('Soak test completed - check for memory leaks and performance degradation');
}
