# ui-copilotkit isolated UI/protocol experiment

This branch uses a fixed synthetic AnswerEnvelope: **zero model calls, zero model cost**. It measures component, transport and lifecycle integration, not dataset answer quality. The main application is untouched.

## Reproduce

Node 24.18.0, Python 3.12.3. Run `npm ci`; `python3 -m venv .venv`; `.venv/bin/pip install -r requirements.txt`. Start `.venv/bin/uvicorn benchmark.server:app --port 8102` and `npx vite --host localhost --port 5174`. Also start `COPILOTKIT_TELEMETRY_DISABLED=true npx tsx benchmark/runtime.ts` on 4102. Browser origins localhost and 127.0.0.1 are explicitly supported.

Run `npm test` (TypeScript), `npm run build`, then open the app in the agent-browser session `ui-rich-ck` and run `npm run test:browser`. Select alice before a clean suite; each page load creates a separate CopilotKit fixture thread. `benchmark/capture_audit.py copilotkit` captures matched desktop/mobile baseline, coordinated selection and evidence drawer PNGs. CopilotKit additionally supports `?a2ui`, `?probe`, `python3 benchmark/a2ui_probe_check.py` and `python3 benchmark/capture_audit.py a2ui`.

All current-audit PNGs use Bob, revision 2, values 18/20; desktop 1440×1000 and mobile 390×844. The manifests record assertions, exact commands, viewport measurements and axe results. Main report: /home/harshsanghavi/orca/projects/asset-copilot-hackathon/agent-memory/ui-experiments.md.

## Contract and results

Both candidates share fixture.json/server.py/shared.tsx/rich_browser.py/capture_audit.py. Python uses actual ag-ui-protocol events and EventEncoder. Direct browser uses real HttpAgent; CopilotKit uses real self-hosted TS runtime, CopilotChat and useRenderTool. The same Ant Design 6.6.6 + ECharts 6.1.0 + echarts-for-react 3.0.6 renderer provides five panels, sort/filter, coordinated selection, evidence drawer and responsive cards. Map boundary and evidence are visibly synthetic. Domain schema validation guards complete envelope/rows/references/revisions, with block-level invalid component isolation.

`results/validation-summary.json` records final commands/outcomes. Both TypeScript and build pass. Rich browser assertions pass for five panels, one invalid block/four siblings, actual table sort/filter, coordinated status/line SVG/map labels, Drawer inspection/Escape/reset, missing-terminal interruption, fresh-run replay, revision update and delayed-stream user switching. A2UI uses maintained React/core 0.14.0 and a single custom EvidenceDashboard catalog component bound through MessageProcessor; incremental update preserves the existing surface/answer DOM and deletion removes it. This **does not** prove independent A2UI component/layout composition or CopilotKit bundled adapter interoperability.

Current desktop/mobile axe checks have zero violations, with SVG contrast verification incomplete; no full accessibility certification is claimed. Initial contrast/link/button-label failures were fixed with shared theme tokens and the supported CopilotChat `input` slot. Earlier primitive build/browser files and failed navigation/selector attempts are historical evidence; prefer current-audit manifests and validation-summary.json for final state. A short transient mobile overflow during Drawer/resize settling was observed; capture now waits for stable no-overflow layout.

Demo headers are not authentication. Shared revision is in-memory synthetic state, not a durable correction ledger. Replay is a new fixture run, not event-offset resume or saved reload restoration. Production auth, concurrency, private evidence lookup, retention and real Q1–Q18 answers are untested. Timings include artificial waits/CLI operations and must not rank latency. Services are kept only for the coordinator's visual audit and stopped on its cleanup signal.

## Compatibility and maintenance

CopilotKit 1.79.1 pins AG-UI client 1.0.2; the root client is aligned to avoid nominal private-class type errors. Maintained A2UI 0.14.0 needs Zod 3.25.76; root Zod is aligned, avoiding the prior excessive-instantiation failure from mixed Zod versions without disabling type checks. Its bundled A2UI adapter still uses an older separate core and is not the tested maintained-renderer path.

Build outputs warn about large chunks; no bundle optimization or startup latency study ran. npm audit returns measured advisories (raw JSON retained), which need review before a future deployment; no package-count winner is inferred. The tested component packages are MIT (CopilotKit/Ant Design) or Apache-2.0 (A2UI/ECharts); installed package metadata was checked. No packages, venvs, logs, caches, secrets or raw dataset are committed.

## Wide rich-response layout after visual audit

The coordinator observed the default 768px message column weakened dashboard scan density. The final `wide-answers` theme widens only the scroll-content answer region, while assistant prose, user message measure and standard composer retain readable widths. At 1440×1000 the answer is 1380px with three ~449px columns and composer textarea 622px; mobile still stacks 318px cards with no document overflow. Standard chat/hooks are retained. `results/current-audit-*` preserves the narrow before state (commit 0c1d3bd); `results/wide-audit-*` is the final after state for CopilotKit and A2UI, including selection/evidence variants and full zero-violation axe receipts. This is scoped styling against pinned CopilotKit DOM/test IDs, which should be rechecked on upgrades.

Use `UI_CAPTURE_PREFIX=wide-audit python3 benchmark/capture_audit.py copilotkit` or `a2ui` to reproduce the final matched captures. A2UI remains visually identical because both paths render the same dashboard; no independent-component composition advantage is claimed.
