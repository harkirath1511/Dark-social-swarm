import assert from 'node:assert/strict';

process.env.TZ = 'UTC';

const { formatLocalTime } = await import('../lib/date-utils.mjs');

assert.equal(
  formatLocalTime('2026-09-05T09:10:50Z', 'en-US'),
  'Sep 5, 2026, 09:10 AM',
  'formats an ISO timestamp into a compact local date and time',
);

assert.equal(
  formatLocalTime('not-a-date', 'en-US'),
  'Recent',
  'uses a readable fallback for malformed timestamps',
);

console.log('date utility tests passed');
