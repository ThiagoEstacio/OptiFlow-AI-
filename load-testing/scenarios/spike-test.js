// SmartPort Spike Test
// Tests system behavior under sudden traffic spikes
// Run with: k6 run spike-test.js

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate } from 'k6/metrics';

const errorRate = new Rate('errors');

// Spike test configuration: Sudden increase then decrease
export const options = {
  stages: [
    { duration: '1m', target: 10 },   // Normal load
    { duration: '30s', target: 200 }, // SPIKE to 200 users
    { duration: '3m', target: 200 },  // Stay at spike
    { duration: '30s', target: 10 },  // Drop back to normal
    { duration: '2m', target: 10 },   // Recover
    { duration: '1m', target: 0 },    // Ramp down
  ],
  thresholds: {
    'http_req_duration': ['p(95)<1500'],  // Allow higher latency during spike
    'http_req_failed': ['rate<0.05'],     // Accept 5% errors during spike
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

  // Simulate mixed workload during spike
  const operations = [
    () => http.get(`${BASE_URL}${API_PREFIX}/sites/`, { headers }),
    () => http.get(`${BASE_URL}${API_PREFIX}/devices/`, { headers }),
    () => http.get(`${BASE_URL}${API_PREFIX}/tags/`, { headers }),
    () => http.get(`${BASE_URL}/health`),
  ];

  // Execute random operation
  const operation = operations[Math.floor(Math.random() * operations.length)];
  const res = operation();

  check(res, {
    'status is 200 or 429': (r) => r.status === 200 || r.status === 429,
    'response under 2s': (r) => r.timings.duration < 2000,
  }) || errorRate.add(1);

  sleep(Math.random() * 2); // Random sleep 0-2s
}
