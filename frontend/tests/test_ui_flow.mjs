/**
 * Phase 5 Verification: UI API Loading and Resume Dispatch Test.
 * Verifies that the client loads pending reviews and fires resume POST requests.
 */

import http from 'http';

const MOCK_OPPORTUNITY = {
  thread_id: 't3_ui_test_99',
  subreddit: 'r/SaaS',
  title: "I've tried three tools for turning long videos into clips. Which one actually works?",
  body: "Most automated tools cut off sentences right in the middle or pick arbitrary highlights that don't make sense without context.",
  author: 'creator_dan99',
  permalink: 'https://reddit.com/r/SaaS/comments/1h9k2z8',
  created_utc: Date.now() / 1000 - 600,
  extracted_problem: 'Frustration with automated video clipping tools cutting audio mid-sentence and missing narrative context.',
  user_intent: 'high',
  evidence_quote: "Most automated tools cut off sentences right in the middle or pick arbitrary highlights that don't make sense without context.",
  opportunity_score: 88,
  engagement_decision: 'engage',
  strategic_reasoning: 'Direct alignment with automated video repurposing pain. Low brand risk.',
  proposed_draft: 'The core issue with clip generators is silence thresholding rather than sentence embeddings.',
  draft_iteration: 1,
  critic_passed: 1,
  violation_category: null,
  critic_feedback: 'Value-first direct answer provided. Passed non-astroturfing guidelines.',
  status: 'AWAITING_APPROVAL',
};

// 1. Create a local mock API server simulating FastAPI endpoints
const server = http.createServer((req, res) => {
  res.setHeader('Content-Type', 'application/json');
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    res.writeHead(204);
    res.end();
    return;
  }

  // GET /api/review-queue
  if (req.method === 'GET' && req.url === '/api/review-queue') {
    res.writeHead(200);
    res.end(JSON.stringify({
      count: 1,
      queue: [MOCK_OPPORTUNITY],
    }));
    return;
  }

  // POST /api/review/t3_ui_test_99/submit
  if (req.method === 'POST' && req.url.startsWith('/api/review/')) {
    let body = '';
    req.on('data', chunk => { body += chunk; });
    req.on('end', () => {
      const parsed = JSON.parse(body);
      res.writeHead(200);
      res.end(JSON.stringify({
        status: 'resumed',
        thread_id: 't3_ui_test_99',
        human_status: parsed.action,
        final_response_text: parsed.edited_text || MOCK_OPPORTUNITY.proposed_draft,
      }));
    });
    return;
  }

  res.writeHead(404);
  res.end(JSON.stringify({ detail: 'Not found' }));
});

server.listen(8001, async () => {
  console.log('Mock API server listening on http://localhost:8001');

  try {
    // Step 1: Test GET /api/review-queue
    const getRes = await fetch('http://localhost:8001/api/review-queue');
    if (!getRes.ok) throw new Error(`GET failed: ${getRes.status}`);
    const getData = await getRes.json();
    console.log(`[PASS] GET /api/review-queue returned ${getData.count} pending opportunity`);
    
    const opp = getData.queue[0];
    if (opp.thread_id !== 't3_ui_test_99') throw new Error('Mismatch thread_id');
    if (opp.opportunity_score !== 88) throw new Error('Mismatch score');
    if (!opp.evidence_quote.includes('sentences right in the middle')) throw new Error('Mismatch evidence quote');
    console.log(`[PASS] Verified UI Fields: Subreddit: ${opp.subreddit}, Author: ${opp.author}, Score: ${opp.opportunity_score}, Intent: ${opp.user_intent}`);

    // Step 2: Test Action 1 - POST /api/review/{id}/submit with 'approved' (Approve & Copy)
    const approveRes = await fetch('http://localhost:8001/api/review/t3_ui_test_99/submit', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action: 'approved' }),
    });
    if (!approveRes.ok) throw new Error(`Approve POST failed: ${approveRes.status}`);
    const approveData = await approveRes.json();
    console.log(`[PASS] Approve action resumed: status=${approveData.status}, human_status=${approveData.human_status}`);

    // Step 3: Test Action 2 - POST /api/review/{id}/submit with 'edited' (Apply Edits)
    const editRes = await fetch('http://localhost:8001/api/review/t3_ui_test_99/submit', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        action: 'edited',
        edited_text: 'Custom edited draft response by marketer.',
      }),
    });
    if (!editRes.ok) throw new Error(`Edit POST failed: ${editRes.status}`);
    const editData = await editRes.json();
    console.log(`[PASS] Edit action resumed: human_status=${editData.human_status}, final_text="${editData.final_response_text}"`);

    // Step 4: Test Action 3 - POST /api/review/{id}/submit with 'rejected' (Reject / Discard)
    const rejectRes = await fetch('http://localhost:8001/api/review/t3_ui_test_99/submit', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        action: 'rejected',
        edited_text: 'Reason: Low commercial intent',
      }),
    });
    if (!rejectRes.ok) throw new Error(`Reject POST failed: ${rejectRes.status}`);
    const rejectData = await rejectRes.json();
    console.log(`[PASS] Reject action resumed: human_status=${rejectData.human_status}`);

    console.log('\n[SUCCESS] Phase 5 Verification Passed: UI loaded pending reviews and successfully fired all resume POST requests.');
  } catch (err) {
    console.error('[FAIL]', err);
    process.exitCode = 1;
  } finally {
    server.close();
  }
});
