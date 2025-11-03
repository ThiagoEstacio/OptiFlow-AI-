// SmartPort Stress Test
// Tests system behavior under extreme load
// Run with: k6 run stress-test.js

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate } from 'k6/metrics';

const errorRate = new Rate('errors');

// Stress test configuration: Gradually increase to breaking point
export const options = {
  stages: [
    { duration: '2m', target: 50 },   // Ramp up to 50 users
    { duration: '5m', target: 50 },   // Stay at 50 users
    { duration: '2m', target: 100 },  // Ramp up to 100 users
    { duration: '5m', target: 100 },  // Stay at 100 users
    { duration: '2m', target: 200 },  // Ramp up to 200 users
    { duration: '5m', target: 200 },  // Stay at 200 users (stress)
    { duration: '2m', target: 300 },  // Push to 300 users
    { duration: '5m', target: 300 },  // Stay at 300 users (extreme stress)
    { duration: '5m', target: 0 },    // Ramp down to 0 users
  ],
  thresholds: {
    'http_req_duration': ['p(95)<1000', 'p(99)<2000'], // Allow higher latency
    'http_req_failed': ['rate<0.05'],  // Accept 5% error rate under stress
  },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';
const API_PREFIX = '/api/v1';

export function setup() {
  const loginRes = http.post(`${BASE_URL}${API_PREFIX}/auth/login`, {
    username: 'testuser',
    password: 'testpass123',
  });

  return { token: loginRes.json('access_token') };
}

export default function (data) {
  const headers = {
    'Authorization': `Bearer ${data.token}`,
    'Content-Type': 'application/json',
  };

  // Heavy read operations
  const endpoints = [
    `${BASE_URL}${API_PREFIX}/organizations/`,
    `${BASE_URL}${API_PREFIX}/sites/`,
    `${BASE_URL}${API_PREFIX}/devices/`,
    `${BASE_URL}${API_PREFIX}/tags/`,
    `${BASE_URL}/health`,
  ];

  // Randomly hit endpoints
  const endpoint = endpoints[Math.floor(Math.random() * endpoints.length)];
  const res = http.get(endpoint, { headers });

  check(res, {
    'status is 200 or 429': (r) => r.status === 200 || r.status === 429, // Allow rate limiting
    'response time under 2s': (r) => r.timings.duration < 2000,
  }) || errorRate.add(1);

  sleep(0.5); // Shorter sleep for stress
}
