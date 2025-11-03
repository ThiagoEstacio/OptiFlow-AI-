// SmartPort API Load Test - Base Configuration
// Run with: k6 run load-test.js

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate } from 'k6/metrics';

// Custom metrics
const errorRate = new Rate('errors');

// Test configuration
export const options = {
  stages: [
    { duration: '2m', target: 10 },  // Ramp up to 10 users
    { duration: '5m', target: 10 },  // Stay at 10 users
    { duration: '2m', target: 50 },  // Ramp up to 50 users
    { duration: '5m', target: 50 },  // Stay at 50 users
    { duration: '2m', target: 100 }, // Ramp up to 100 users
    { duration: '5m', target: 100 }, // Stay at 100 users
    { duration: '2m', target: 0 },   // Ramp down to 0 users
  ],
  thresholds: {
    'http_req_duration': ['p(95)<500'], // 95% of requests should be below 500ms
    'http_req_failed': ['rate<0.01'],    // Error rate should be less than 1%
    'errors': ['rate<0.1'],              // Custom error rate
  },
};

// Configuration
const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';
const API_PREFIX = '/api/v1';

// Test data
let authToken = '';
let organizationId = '';
let siteId = '';
let deviceId = '';

export function setup() {
  // Setup: Login and create test resources
  const loginRes = http.post(`${BASE_URL}${API_PREFIX}/auth/login`, {
    username: 'testuser',
    password: 'testpass123',
  });

  check(loginRes, {
    'login successful': (r) => r.status === 200,
  });

  const token = loginRes.json('access_token');

  return { token };
}

export default function (data) {
  const headers = {
    'Authorization': `Bearer ${data.token}`,
    'Content-Type': 'application/json',
  };

  // Test 1: List organizations
  let res = http.get(`${BASE_URL}${API_PREFIX}/organizations/`, { headers });
  check(res, {
    'list organizations status is 200': (r) => r.status === 200,
    'list organizations response time OK': (r) => r.timings.duration < 500,
  }) || errorRate.add(1);

  sleep(1);

  // Test 2: List sites
  res = http.get(`${BASE_URL}${API_PREFIX}/sites/`, { headers });
  check(res, {
    'list sites status is 200': (r) => r.status === 200,
    'list sites response time OK': (r) => r.timings.duration < 500,
  }) || errorRate.add(1);

  sleep(1);

  // Test 3: List devices
  res = http.get(`${BASE_URL}${API_PREFIX}/devices/`, { headers });
  check(res, {
    'list devices status is 200': (r) => r.status === 200,
    'list devices response time OK': (r) => r.timings.duration < 500,
  }) || errorRate.add(1);

  sleep(1);

  // Test 4: List tags
  res = http.get(`${BASE_URL}${API_PREFIX}/tags/`, { headers });
  check(res, {
    'list tags status is 200': (r) => r.status === 200,
    'list tags response time OK': (r) => r.timings.duration < 500,
  }) || errorRate.add(1);

  sleep(1);

  // Test 5: Health check
  res = http.get(`${BASE_URL}/health`);
  check(res, {
    'health check status is 200': (r) => r.status === 200,
    'health check response time OK': (r) => r.timings.duration < 100,
  }) || errorRate.add(1);

  sleep(2);
}

export function teardown(data) {
  // Cleanup: Could delete test resources here
  console.log('Load test completed');
}
