# UI integration experiments — final bounded results

17 Oct 2026. **UI/protocol and component validation only: zero model calls and zero model cost.** These isolated experiments replay a synthetic AnswerEnvelope, not answers to the hackathon dataset. The main application, raw data, root secrets and diagrams/ were untouched. No runtime model or embedding model was added; only the coordinator checks the selected Gemma provider/key.

## Decision for plan review

**Measured functional tie for the rich dashboard; select the tested CopilotKit + AG-UI + wide rich-response layout + application-owned Ant Design/ECharts component catalog for the conversational copilot plan.** The recommendation is based on its working chat/tool rendering and the user's enterprise interaction priority, not package count or scripted durations. Direct AG-UI is a fully credible rich baseline: AG-UI does not limit panel count or component richness. Both use exactly the same enterprise renderer, so the visual styling is shared rather than a framework advantage.

Root's visual audit found that the default CopilotKit 768px message column made the dashboard narrower/longer than the direct three-column canvas. The final CopilotKit `wide-answers` theme fixes that measured weakness: at 1440×1000, the answer is **1380px wide with three ~449px columns**, while assistant prose and the standard composer retain readable widths (composer textarea measured 622px). Mobile still stacks 318px cards with no document overflow. CopilotKit keeps actual user/assistant history, composer and standard render hooks. Before/after PNGs and geometry are retained; this is tested layout customization, not an assertion that CopilotKit inherently looks better. Root owns the independent Product Design audit.

**A2UI is a compatible optional composition, not a competing transport.** CopilotKit + AG-UI + maintained A2UI React + the same AntD/ECharts custom dashboard works, including incremental same-surface updates. The experiment registers one EvidenceDashboard catalog component, so it does **not** establish independently composable A2UI cards/tables/charts, arbitrary model-authored layouts, or superiority in layout flexibility. Keep that gap explicit; do not sell the wrapper as proof of unbounded generative UI.

## Branches and durable artifacts

| Complete combination | Experiment path | Final experiment commit |
|---|---|---|
| Python AG-UI HTTP → browser HttpAgent → typed AntD/ECharts dashboard | `/home/harshsanghavi/orca/projects/asset-copilot-experiments/ui-agui` | `b3ce62044f9f84659fa539525b056723ff4db22d` |
| Python AG-UI HTTP → self-hosted CopilotKit TS runtime → CopilotChat/useRenderTool → same dashboard; optional maintained A2UI custom catalog | `/home/harshsanghavi/orca/projects/asset-copilot-experiments/ui-copilotkit` | `0486915fb6f280c198b7e94a47990b6d68087831` |

Earlier paused checkpoints `cfef358` and `0312f54` preserve the recovery state. Each final branch has benchmark/README.md, exact lockfiles, reproducible scripts and raw results. Coordinator-created untracked AGENTS.md files remain uncommitted; node_modules/venvs/logs/caches are ignored. No publishing was performed.

Raw final checks: `results/validation-summary.json`, `typecheck.txt`, `final-build.txt`, `rich-browser-results.json`. Additional A2UI checks: `a2ui-rich-browser-results.json`, `a2ui-incremental-results.json`. Primitive browser-results/build files and earlier failed navigation/selector attempts are historical checkpoints, not final acceptance evidence.

## Actual feature/test matrix

Both branches share fixture.json, server.py, shared.tsx and rich_browser.py. Capture scripts exercise the same scenario and viewport sizes; the CopilotKit version additionally records wide-layout geometry and supports before/after filename prefixes. Python uses real `ag-ui-protocol` typed run/text/tool events and EventEncoder over HTTP/SSE. Direct browser uses actual HttpAgent. CopilotKit uses a supported self-hosted TypeScript runtime with InMemoryAgentRunner, actual CopilotChat and registered useRenderTool; this is not an install-only test, custom-SSE imitation or development-only self-managed provider shortcut. No Intelligence service key was required for the tested TS path.

| Local check | Direct rich AG-UI | CopilotKit rich AG-UI | CopilotKit + maintained A2UI dashboard |
|---|---|---|---|
| Five validated inline panels in one answer | Passed | Passed | Passed |
| One unsupported component rejected; four siblings usable | Passed | Passed | Passed |
| AntD table descending sort + text filter | Passed | Passed | Passed |
| Row selection coordinates status, actual line SVG value and map labels | Passed | Passed | Passed |
| Evidence Drawer record inspection; Escape close; reset | Passed | Passed | Passed |
| Partial tool JSON followed by EOF is a visible failure; no new factual dashboard | Passed | Passed | Passed |
| Fresh-run fixture replay after interruption | Passed | Passed | Passed |
| Revision 2 updates value 15→18 at one consistent result revision | Passed | Passed | Passed |
| Switch Alice→Bob during delayed stream; Alice panels absent; Bob answer renders | Passed | Passed | Passed |
| TypeScript check and production Vite build | Passed | Passed | Passed as part of same CopilotKit build |
| Desktop + mobile WCAG2 A/AA axe scan after fixes | Zero violations; incomplete contrast checks remain | Same | Same |
| Maintained A2UI incremental update keeps same surface/answer DOM; delete removes DOM | Not applicable | Not applicable | Passed independent probe |
| Independently composable A2UI multi-component/layout updates | Not applicable | Not applicable | **Untested** |

Assertions and exact agent-browser commands/exit/output are retained in the raw JSON. CopilotKit's missing-terminal error text is now explicitly asserted, together with unchanged factual dashboard count; the earlier checkpoint only captured that screen. Its partial-JSON parser can deliver a partially parsed object after stream failure; the domain schema rejects that object visibly instead of displaying numbers. Direct path explicitly asserts missing RUN_FINISHED.

The rich renderer uses real Ant Design Card/Statistic/Table/Input/Select/Drawer/Alert and real ECharts line, heatmap and geographic scatter. The map uses visibly labeled synthetic local GeoJSON, not real fleet geospatial coverage. Complete envelopes/rows, component union, references and revisions are validated before factual panels render. Table, chart values, accessible text fallbacks and source receipts use the same effective result. Charts use fresh option replacement to avoid unintended stale option merges. This two-record fixture tests compatibility, not fleet-scale performance or analytical correctness on actual data.

Shared revision is in-memory synthetic server state: revision command advances to 2 and later Bob requests use it. It is **not** a durable correction ledger, real query result or shared-memory implementation. Demo user headers are a picker identity, not authentication. Runtime uses per-demo-user runners and request-scoped HttpAgent instances; frontend checks scope and discards/unmounts stale prior-user results. Adversarial guessed-ID access, private evidence authorization, concurrency, retention and durable reload restoration remain untested. Replay is a new run, not event-offset resume.

## Actual visual evidence

All **current-audit** before and **wide-audit** after captures use Bob, revision 2, values 18/20, desktop **1440×1000** and mobile **390×844**. The final comparison is direct current-audit versus CopilotKit/A2UI wide-audit; the narrow default is retained as the before state at commit 0c1d3bd. Each includes a default dashboard, coordinated TEST-02 selection and evidence drawer. These are running-browser screenshots, not generated mockups.

| Combination | Desktop | Mobile | Manifest |
|---|---|---|---|
| Direct rich AG-UI | [PNG](../../asset-copilot-experiments/ui-agui/results/current-audit-agui-desktop.png) | [PNG](../../asset-copilot-experiments/ui-agui/results/current-audit-agui-mobile.png) | `ui-agui/results/current-audit-agui-manifest.json` |
| CopilotKit rich | [PNG](../../asset-copilot-experiments/ui-copilotkit/results/wide-audit-copilotkit-desktop.png) | [PNG](../../asset-copilot-experiments/ui-copilotkit/results/wide-audit-copilotkit-mobile.png) | `ui-copilotkit/results/wide-audit-copilotkit-manifest.json` |
| CopilotKit + maintained A2UI | [PNG](../../asset-copilot-experiments/ui-copilotkit/results/wide-audit-a2ui-desktop.png) | [PNG](../../asset-copilot-experiments/ui-copilotkit/results/wide-audit-a2ui-mobile.png) | `ui-copilotkit/results/wide-audit-a2ui-manifest.json` |

Paths above are relative to this report. Each results folder also has matching `...-selected.png` and `...-evidence.png` variants. Use `current-audit-agui-*` for direct, `wide-audit-copilotkit-*` and `wide-audit-a2ui-*` for the final configured shell; all `current-audit-copilotkit/a2ui-*` before files remain available. The manifests contain all absolute PNG paths, URLs, viewport measurements, complete axe results and commands. Earlier final-desktop.png screenshots were also shown directly to the user when requested.

Measured settled mobile `scrollWidth === innerWidth === 390` for all three combinations. Direct cards are 370px wide; CopilotKit/A2UI cards are 318px inside the chat message. The table deliberately has its own horizontal scrolling region. A transient 10px overflow occurred while the direct Drawer/resize settled; the final capture script waits for a stable no-document-overflow state and passes. Screenshots show stacked usable cards; no full screen-reader/usability study is claimed.

Real axe 4.12.1 desktop/mobile scans now report **zero violations** in all three combinations. Initial measured failures were the AntD statistic caption and well-link contrast, plus two unnamed default CopilotKit chat buttons. Darker theme tokens and supported CopilotChat `input` slot labels fix them. SVG text/select overlap checks remain in the incomplete contrast category and require manual assessment. Escape closing the Drawer is tested; complete keyboard and screen-reader coverage is not.

## Verified compatible versions, commands and maintenance

Node **24.18.0**, Python **3.12.3**, React/ReactDOM **19.2.4**, Vite **7.3.1**, TypeScript **5.9.3**; Python `ag-ui-protocol` **1.0.0** with complete pinned requirements.txt. Shared UI: Ant Design **6.6.6**, ECharts **6.1.0**, echarts-for-react **3.0.6**.

Direct branch: `@ag-ui/client` **1.0.3**, Zod **4.3.6**. CopilotKit branch: react-core/react-ui/runtime **1.79.1**, aligned `@ag-ui/client` **1.0.2**, Express **5.2.1**, tsx **4.21.0**, Zod **3.25.76**. Optional maintained A2UI React/core **0.14.0**. Catalog wire messages in this test use package-documented **v0.9**, not a claim that v0.9.1 was tested. Exact dev-type package pins are in package-lock.json.

Registry metadata was checked and installed packages were actually exercised. Two meaningful compatibility failures were fixed without disabling type checks: CopilotKit's exact AG-UI 1.0.2 pin conflicts nominally with root HttpAgent 1.0.3 private types, and mixed Zod 4 plus maintained A2UI's required Zod 3 caused excessive generic type instantiation. Aligning the CopilotKit root SDK/Zod makes `npm run typecheck` pass. Its bundled A2UI adapter still has separate older core 0.10.4; that adapter is **not** the maintained renderer tested here and should not be conflated with it.

The wide response theme scopes CSS to the chat scroll-content region and message/prose selectors of the pinned package; upgrades must recheck those DOM/test-ID hooks. The ordinary narrow composer and standard CopilotChat lifecycle are retained.

Other interop lessons: mount the Express runtime router with basePath intact; useRenderTool render props contain `parameters`; supported chat input customization uses the `input` slot (a similarly named inputProps prop did not add button labels); disable development inspector overlays in the fixture; validate partial tool payloads; distinguish AntD hidden measurement rows from visible data in browser assertions. CORS initially allowed only localhost; both loopback hostnames are now explicitly supported and a real 127.0.0.1 OPTIONS receipt is saved.

Reproduction commands are `npm ci`, `python3 -m venv .venv`, `.venv/bin/pip install -r requirements.txt`, `.venv/bin/uvicorn benchmark.server:app --port 8101` (direct) / `8102` (CopilotKit), `npx vite --host localhost --port 5173` / `5174`; CopilotKit also `COPILOTKIT_TELEMETRY_DISABLED=true npx tsx benchmark/runtime.ts`. Then `npm test`, `npm run build`, `npm run test:browser`; see branch README for named browser sessions and A2UI probe/capture commands.

Final builds passed (direct log **20.75s**, CopilotKit wide-layout log **30.71s**) and warn about large output chunks. Build time, package count and scripted suite duration are **not** startup/runtime latency or visual-quality rankings. Suites deliberately include waits/animation/CLI overhead; exact elapsed values are recorded in the raw results. Work spans approximately 12:08–12:53 IST including crash recovery and a user-requested pause; no reliable active-work stopwatch was retained.

Final npm audit raw JSON records direct **2 advisories** (1 low/1 high), CopilotKit+A2UI **20** (11 low/6 moderate/3 high). These are actual package-audit results, not demonstrated exploits; deployment dependency review remains future work. Package metadata verified MIT for CopilotKit/AntD and Apache-2.0 for A2UI/ECharts. No paid service was used. Runtime telemetry was disabled explicitly; default development browser activity earlier included CDN/fonts/telemetry, so these prototypes are **not** an offline-readiness claim.

## Primary research and documented examples

- [AG-UI HttpAgent reference](https://docs.ag-ui.com/sdk/js/client/http-agent): standard HTTP event client used locally.
- [CopilotKit runtime guide](https://docs.copilotkit.ai/backend/copilot-runtime), [CopilotChat](https://docs.copilotkit.ai/reference/components/CopilotChat), [render tool APIs](https://docs.copilotkit.ai/reference/hooks/useRenderToolCall): TS self-hosting and chat rendering verified against actual installed exports/types and runs.
- [Official CopilotKit showcase](https://showcase.copilotkit.ai/integrations): documented examples distinguish named-tool rendering, a fixed A2UI tree with streamed data, independent dynamic custom catalogs and slot customization. Our local A2UI wrapper is closest to constrained fixed composition; the showcase's dynamic examples are capability references, not local test results or an independent customer case study.
- [Ant Design enterprise patterns](https://ant.design/docs/spec/overview/), [table API](https://ant.design/components/table/), [Apache ECharts accessibility guidance](https://echarts.apache.org/handbook/en/best-practices/aria/): inform consistent enterprise controls, interaction and aria/decal configuration; local audits were still necessary.
- [A2UI renderer matrix](https://a2ui.org/reference/renderers/) and [maintained React source](https://github.com/a2ui-project/a2ui/tree/main/typescript/renderers/react): actual custom-catalog package was run, not inferred from transport support. Basic catalog is not a ready-made oil-well analytic component library.
- [When Interfaces Speak / GenUI-Harness](https://arxiv.org/html/2610.11123v1): separates evidence/tool work from generated UI and evaluates task outcomes. Transferable lesson is to ground UI in records and test interactions, not only successful rendering. Its generated-code/RL/database metrics, source-aware simulator and selected usable-interface survey do not prove effectiveness of our typed renderer; no paper or vendor number is presented as a local score.

Ant Design is the actual tested rich library. shadcn/Radix and Mantine remain untested alternatives; there is no measured library winner over them. Future production code can use a custom shell or broader A2UI catalog, but those require their own implementation evidence rather than an assumption of greater richness.

## Boundary and handoff

The authorized bounded UI experiment is complete. The recommended **complete compatible combination** is Python AG-UI + self-hosted CopilotKit TypeScript runtime + React/CopilotChat + typed AntD/ECharts dashboard, with maintained A2UI as a proven optional single-dashboard binding route. Keep direct rich AG-UI as the functional baseline. Root may revise the visual/shell preference after its screenshot audit; shared component appearance and the untested independent A2UI layout gap must stay visible.

Future main implementation still needs approved plan review, real tool/result/evidence contracts, Gemma-only endpoint/schema checks by the proper track, durable shared knowledge/private memory, real production auth and source viewer, source-independent Q1–Q18 acceptance, richer maps, larger fixtures, saved reload restoration, concurrency, manually assessed accessibility and dependency review. None is claimed complete by this prototype.

Cleanup completed after the coordinator confirmed visual review and copied captures into root experiments/: exactly the two owned Python servers, two Vite servers and TypeScript runtime were stopped; no listeners remain on 5173/5174/8101/8102/4102. All owned named browser sessions were closed and the coordinator's separate review browser was left untouched. At the coordinator's explicit authorization, `skills/generative-ui/SKILL.md` was updated to the measured wide CopilotKit + AG-UI + AntD/ECharts direction, retaining the rich direct baseline, A2UI wrapper/composition distinction and strict validation limits. Its quick_validate.py check passes. No application implementation or new alternative-library comparison was started by this worker.
