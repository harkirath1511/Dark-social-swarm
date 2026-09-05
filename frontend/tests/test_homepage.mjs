import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';

const port = 3101;
const baseUrl = `http://127.0.0.1:${port}`;
const server = spawn('./node_modules/.bin/next', ['dev', '-p', String(port)], {
  cwd: process.cwd(),
  stdio: ['ignore', 'pipe', 'pipe'],
  detached: true,
});

let output = '';
server.stdout.on('data', (chunk) => { output += chunk.toString(); });
server.stderr.on('data', (chunk) => { output += chunk.toString(); });

async function waitForHomepage() {
  const deadline = Date.now() + 30_000;
  while (Date.now() < deadline) {
    try {
      const response = await fetch(baseUrl);
      const html = await response.text();
      if (response.ok && html.includes('<main')) return html;
    } catch {
      // The server is still compiling or starting.
    }
    await new Promise((resolve) => setTimeout(resolve, 250));
  }
  throw new Error(`Next.js did not serve the homepage.\n${output}`);
}

try {
  const html = await waitForHomepage();
  const visibleText = html.replace(/<[^>]+>/g, ' ');
  assert.match(visibleText, /See intent\s+before\s+it becomes a lead/i);
  assert.match(html, /href="\/review"/);
  assert.match(html, /3 signals ready for human review/i);
  assert.match(html, /aria-label="Global community signal map"/);
  assert.match(visibleText, /Community signal network/i);
  assert.match(visibleText, /How the swarm works/i);
  assert.match(visibleText, /Built for human judgment/i);
  console.log('[PASS] Homepage exposes the signal-intelligence CTA and review status.');
} catch (error) {
  console.error(error);
  process.exitCode = 1;
} finally {
  if (server.exitCode === null) {
    await new Promise((resolve) => {
      server.once('exit', resolve);
      process.kill(-server.pid, 'SIGTERM');
    });
  }
}
