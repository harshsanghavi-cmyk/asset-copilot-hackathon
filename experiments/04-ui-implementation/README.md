# Frontend implementation evidence

Stable preview: http://127.0.0.1:5192. Development: http://127.0.0.1:5190. Companion: http://127.0.0.1:4190/health. All bind loopback and remain running for review; Python8000 is peer-owned. Nothing is published. See [the screenshot gallery](screenshots.md) and [the implementation report](../../agent-memory/ui-implementation.md).

Current backend uses Google AI Studio Gemma4 26B A4B and the600-asset Jan15,2027 dataset. Historical31B failures and200-asset responses remain labeled archived evidence. Real26B greeting succeeded; recorded browser behavior does not establish model reliability or Q1–Q18 correctness.

Reproduce from project root:

```
npm ci --prefix frontend
npm test --prefix frontend
npm run typecheck --prefix frontend
npm run build --prefix frontend
python3 frontend/tests/browser_check.py
python3 frontend/tests/ui_states.py
python3 frontend/tests/chat_controls.py
python3 frontend/tests/suggestion_pills.py
python3 frontend/tests/pending_history.py
python3 frontend/tests/http_replay_browser.py
python3 frontend/tests/spatial_replay.py
```

Thirty-five unit/protocol tests and the production TypeScript/Vite build pass. `ui-state-results.json` has six passing states, including partial verified records, cooldown and canonical retry. `chat-controls-browser-results.json` covers edit/cancel/branch/original/retry/reload/mobile. `suggestion-pills-browser-results.json` covers read-only history, draft-only pills, privacy, stale receipts, queued deadlines and interrupted recovery using recorded API responses. `delayed-runtime-browser-results.json` records a35-second full HTTP/runtime/SDK/browser replay, one fake agent request and no document reload or model call. `spatial-replay-results.json` retains actual archived200 geographic observations across4 areas without filtering or interpolation. These are sample/recorded tests, not new model calls.

Earlier `browser-results.json` records eight workflows including search, rename, delete confirmation, profile cancellation, coordinated panels, keyboard map/evidence and reduced motion. Recent `a11y-readable-desktop.json` and mobile scans report zero violations and two incomplete manual-review categories; `readable-layout-measurements.json` contains measured font sizes and mobile overflow checks. Old logs/captures remain historical and must not be mistaken for current acceptance.

`live26-greeting-*` captures a successful actual model greeting. `live26-q1-*` preserves a real failed narrative-validation run. `q1-data-unavailable-complete.png` is read-only verification of the current600-asset source-only answer after its backend completion-status repair, with no fabricated pressure data. `live-branch-metadata-results.json` records actual201 branch metadata operations with zero model calls. Independently successful live-generated follow-up suggestions remain unverified by this worker under the final evaluation read-only gate.

The companion has no model credential. The local diagnostic proxy keeps the runtime capability server-side, checks loopback browser provenance and allowlists read-only diagnostics; this is prototype access control, not production authentication. The retrieval-viewer subtree belongs to its separate owner. The assigned executed source walkthrough is [WELL-0001-WALKTHROUGH.md](../05-retrieval-viewer/WELL-0001-WALKTHROUGH.md).
