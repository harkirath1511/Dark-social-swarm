import assert from 'node:assert/strict';
import nextConfig from '../next.config.js';

const rewrites = await nextConfig.rewrites();

assert.ok(
  rewrites.some((rewrite) => rewrite.source === '/api/:path*' && rewrite.destination === 'http://localhost:8000/api/:path*'),
  'Next.js must proxy browser API calls to the FastAPI backend during local development.',
);

console.log('[PASS] Next.js proxies /api requests to FastAPI.');
