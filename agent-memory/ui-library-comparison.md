# OSS UI library comparison — measured followup

17 Oct 2026. Isolated experiments only; main application and earlier UI branches are preserved. **12 successful native Gemma countTokens requests, zero generation requests, no repairs or provider fallback.** Counts are static serialization measurements, not proof that Gemma reliably generates either grammar. Only gemma-4-31b-it was requested; credentials never enter artifacts. The attempt ledger was persisted before each request, with at least2.2seconds between starts. Its12-request cap is exhausted and must not be reset.

## Decision

**Retain the tested wide CopilotKit + Ant Design + Apache ECharts combination, using AG-UI transport and the compact reference-based JSON ViewPlan.** This is a concrete complementary mix: conversational shell, enterprise controls and specialized analytics. Keep the model-visible catalog small and task-specific; adding a UI package does not require exposing every component to the model.

OpenUI and json-render both work as optional composition layers with those same components. They now have real independently composed/reordered panels in the prototype, rather than the earlier A2UI monolithic-dashboard wrapper. Neither produces a visible analytic-panel advantage when the actual components are identical. OpenUI's matched output saving is **13 Gemma tokens, about8%**, over the compact plan; JSON wrapping eliminates that saving. That is insufficient evidence to replace the existing domain validation seam solely for token savings. This is not a verdict that OpenUI or json-render cannot help larger catalogs or different tasks.

If a general JSON component-tree catalog becomes a real requirement, **json-render is the cleaner optional JSON-native extension to evaluate next**: catalog/registry/schema validation and real layout updates work. If compact DSL output over a broad prebuilt catalog becomes a requirement, OpenUI is a credible alternative, with a working CopilotKit integration. Do not stack OpenUI and json-render together for the same answer without a concrete interoperability need. assistant-ui is an alternative chat shell, not an additional analytic catalog to layer on top of CopilotKit.

## Preserved branches and artifacts

| Candidate | Worktree | Commit |
|---|---|---|
| Existing wide CopilotKit reference | `asset-copilot-experiments/ui-copilotkit` | `0486915fb6f280c198b7e94a47990b6d68087831` |
| OpenUI + same CopilotKit/AntD/ECharts | `asset-copilot-experiments/ui-openui` | `be402110eeaa3e6db284a3ce8e68f9d4015b8046` |
| json-render + same CopilotKit/AntD/ECharts | `asset-copilot-experiments/ui-json-render` | `b833e4a357917c15294786a7c6f982d67686f468` |

Paths are under `/home/harshsanghavi/orca/projects/`. Each new branch starts from0486915 and contains reproducible `comparison/` source/config, exact lockfile and `results/library-*` receipts. No dependencies, caches, databases, credentials or raw dataset are committed. Original branches were not edited.

The review copy is `experiments/01-generative-ui/library-comparison/`: baseline/OpenUI/json-render desktop/mobile PNGs, reordered/evidence variants, this report and README. No files were placed in diagrams/.

## Actual catalog coverage, not a vendor maximum

Registry versions were verified, installed exports inspected and component names counted programmatically.

| Library | Installed version/license | Actual model-visible built-in entries | Coverage and important boundaries |
|---|---|---|---|
| OpenUI react-lang / lang-core | 1.0.1, MIT | Renderer/parser infrastructure; custom catalog in this trial has7 entries | defineComponent/createLibrary, parser and prompt generation; not itself a chart kit |
| OpenUI react-ui General library | 0.18.1, MIT | **82** | Layout10; content11; table-related3; chart-related13; forms19; buttons3; display6; card-related17. These groups include helpers/subcomponents, not82 complete dashboards. |
| OpenUI react-ui Chat library | 0.18.1, MIT | **84** | More chat-oriented sections/follow-ups alongside tables/charts/forms/cards. This is a model-visible generative catalog, not a count of chat-shell primitives. |
| json-render core/react/shadcn | 0.21.1, Apache-2.0 | **36** shadcn definitions | Layout/containers10, content/data/feedback12, form controls7, actions/navigation7. No chart, heatmap or geographic-map definition in that exported36-entry catalog. |
| assistant-ui | MIT, source reviewed only | Not counted as an analytic model catalog | Composable Thread/Message/Composer/tool-render primitives and optional managed cloud; no prototype or token/visual superiority claim in this task. |

OpenUI's chart group contains **9 chart types plus4 series/point helpers**; its table group is Table, EditableTable and Col. Neither inspected OpenUI catalog contains a heatmap or geographic map entry. Both native libraries would need trusted-data adapters for this project's EvidenceRef/ResultSet semantics, and custom domain components for unsupported analytics. The installed native catalogs were **inventoried**, not all rendered or quality-tested.

The actual matched trials expose the same **7-entry subset**: Grid, FocusControl, Status, Table, Line, Heatmap, Map. Five analytic adapters reuse the baseline's real AntD/ECharts Panel implementation. Thus the built-in82/84/36 numbers do not describe what the model saw in the token test or what was displayed. Raw complete inventories are `results/openui-catalog-inventory.json` and `results/json-render-catalog-inventory.json`.

## Fair output serialization measurement

All three representations describe the same useful five panels, separate coordinated FocusControl and three-column Grid, with exactly the same `r1`, `inspection-1` and `rule-1` references. There are **no numeric data arrays, user identities, evidence URLs, generated JavaScript or full AnswerEnvelope** in any measured output. Server-owned fixture values remain outside the model text. Sources are the frozen `comparison/*-output.txt` files, with request hashes in the ledger.

| Equivalent fixed output representation | Gemma output-spec tokens | Relative to compact ViewPlan |
|---|---:|---:|
| Compact reference JSON ViewPlan | **161** | Baseline |
| OpenUI Lang | **148** | 13 fewer, about8.1% |
| JSON object wrapping OpenUI Lang | **173** | 12 more, about7.5% |
| json-render flat JSON snapshot | **242** | 81 more, about50.3% |

JSON wrapping uses `{format:"openui",program:string}`. The wrapper parses strictly, then the inner program passes the actual parser/guard and renders five panels in a real browser. It can preserve the selected endpoint's JSON-object envelope requirement, but retains a second grammar and loses this fixture's output-token advantage. It does not replace server-side AnswerEnvelope assembly or domain validation.

OpenUI's published up-to67% claim is not transferred to this result. Its official benchmark uses GPT-5-family tokenization and data-bearing/JSON-patch examples; this trial uses the verified **Gemma tokenizer** and compact references. Different representation baselines explain why both numbers can differ. [Official benchmark methodology](https://openui.com/docs/openui-lang/benchmarks)

## Input and total counts: explicit configuration caveat

The native count endpoint measured the exact stored instruction texts, output texts and their joined serialization separately. These are not actual chat-generation usage or billed-cost receipts. `sum` below is input plus output segment counts; `joined` includes the common OUTPUT_SPEC separator. Monetary cost was not returned by countTokens.

| Instruction configuration measured | Input/catalog instructions | Output | Segment sum | Joined text | Interpretation |
|---|---:|---:|---:|---:|---|
| Handwritten compact baseline schema/instructions | 158 | 161 |319|323| Task-specific compact plan |
| OpenUI generated7-component prompt, tools/bindings/builtins disabled |818|148|966|970| Generated grammar/schema convenience costs more input in this configuration |
| Same OpenUI prompt + JSON-wrapper instruction |845|173|1018|1022| Wrapper overhead measured separately |
| json-render native generated default7-component prompt |4254|242|4496|4500| **Diagnostic default configuration, NOT an eligible apples-to-apples snapshot-prompt total** |

**Only the output-spec column is a controlled like-for-like encoding comparison.** The baseline prompt was hand-compressed while library prompts were generated, so input totals are not equally optimized minima. In particular, json-render's native default documents **JSONL patch generation**, generic state/edit behavior and built-in capabilities, while the tested fixed renderer accepts a complete snapshot and denies those dynamic features. Its4254-token default is useful configuration evidence, but combining it with our snapshot output does **not** establish an efficient end-to-end model prompt or prove json-render intrinsically needs4496 tokens. An aligned compact snapshot prompt or JSONL-patch experiment was not Gemma-counted within the exhausted12-request budget. No total-efficiency winner is claimed from that row.

The actual OpenUI generated input text remained byte-identical after final Zod alignment, verified in `results/openui-prompt-stability.json`. In the measured OpenUI configuration, saving13 output tokens does not offset the additional instruction text, but caching/amortization and equally tuned prompts were not tested. No generation reliability, first-panel latency, throughput or runtime-latency ranking follows from these static numbers. No model fallback or more requests were used to hide this limitation.

## Real integration and safety checks

OpenUI uses the official **single assistant markdown-renderer slot** in actual CopilotChat, with real createLibrary/defineComponent/createParser/Renderer. json-render uses its actual defineCatalog/defineRegistry/JSONUIProvider/Renderer and catalog validation in the equivalent slot. The unchanged AG-UI Python event emitter/self-hosted CopilotKit TS runtime replays fixed specs; these are not package-install-only or custom-SSE imitations. [OpenUI's CopilotKit integration](https://openui.com/docs/build-agents/copilotkit), [json-render source/API](https://github.com/vercel-labs/json-render)

| Measured local check | OpenUI production preview | json-render production preview |
|---|---|---|
| Five independently registered analytic components plus separate control | Passed | Passed |
| Reverse child order without replacing a monolithic Dashboard | Passed | Passed |
| Change Grid to two columns through spec | Passed | Passed |
| Shared selection updates status and actual map labels | Passed | Passed |
| Evidence drawer resolves synthetic record source | Passed | Passed |
| Unknown component / partial parser input rejected | Passed | Passed |
| Unauthorized result refs render no factual panels | Passed | Passed |
| Cross-user scope and mismatched revision guards | Passed | Passed |
| Revision refresh and user switch during delayed stream | Passed | Passed |
| TypeScript and production Vite build | Passed | Passed |
| Matched desktop/mobile capture, document overflow at390px | No overflow | No overflow |
| Axe WCAG2 A/AA scan on final capture | Zero violations; incomplete contrast remains | Same |

All numeric values and evidence are bound through trusted Scope context from the same frozen synthetic ResultSet/EvidenceRef fixture. The model never selects user, author, revision head or network endpoints. The adapters check own-property reference membership, revision and evidence validity; displayed panel titles come from trusted component kinds. OpenUI's permissive parser is wrapped with strict completeness/error checks and Query/Mutation/function/network syntax rejection; toolProvider is null. json-render's catalog/structure validators plus a local guard deny state/binding/action/network fields. No eval, arbitrary HTML/JS, OpenUI Gateway, Autofix cloud, OUI model, evaluator model or hidden fallback is configured.

These are bounded demo guards, not production authentication or proof of durable private memory. Revision refresh changes trusted synthetic fixture data; it is not a formal correction ledger. Partial responses are withheld until a complete validated spec is available, so native progressive-render timing benefits were not measured. No actual Gemma UI generation or real dataset question was evaluated. Raw parser, domain and browser receipts are in each branch's results/; all browser command/exit/output logs are retained.

## Configuration and interoperability findings

| Combination | Concrete setup | Native support versus custom work |
|---|---|---|
| Existing compact ViewPlan | Domain allowlist/schema, server assembly, trusted React dispatch | Already domain-oriented; ordered blocks and controls remain application-owned |
| OpenUI + existing shell/components | Define7 components; give each its own props-schema identity; createLibrary/root; generated prompt; actual parser guard; one CopilotKit markdown slot; trusted data provider | Library supplies grammar/parser/prompt/renderer. Domain data/evidence adapters, authorization and wide rich-response styling are ours. |
| json-render + existing shell/components | defineCatalog + defineRegistry; JSONUIProvider/Renderer; catalog+structure validation; same trusted provider; snapshot-aware prompt still needs configuration | Library supplies JSON schema/registry/render machinery. Native36 shadcn entries were not substituted for AntD; using those widgets also needs their styling setup. |

Both trials needed a **wide override for a program inside the prose slot**; the earlier tool-renderer wide rule alone left the custom markdown output constrained to768px. Final program canvases measure **1380px with three449px columns** at1440×1000. This is integration styling, not an inherent framework limit or evidence that an extra renderer makes charts prettier.

OpenUI accepted the baseline Zod3 peer range in development, but production bundling failed on missing `zod/v4` mergeDefs. Root Zod4.3.6 fixes the actual build. Reusing the same props-schema object across five defineComponent calls also overwrote schema IDs so only the last panel appeared in parser availability; separate schema identities fix it. These exact interoperability findings are recorded rather than treated as a fabricated benchmark score.

OpenUI's automatic development inspector opened over the evidence drawer during invalid-program tests. Manual enabled=false did not by itself remove that auto-mounted widget in the tested development run; final testing/capture uses the documented **production build/preview**, where the inspector is off. OPENUI_TELEMETRY_DISABLED=1, DO_NOT_TRACK=1 and publishObservability=false are explicit; no Autofix or provider connection was activated. Initial failed development receipts are preserved. [Devtools source/docs](https://github.com/thesysdev/openui/tree/main/packages/devtools), [telemetry controls](https://openui.com/docs/openui-lang/telemetry)

json-render0.21.1 explicitly requires Zod4; its isolated branch uses4.3.6 without forcing incompatible peers. Its default prompt's JSONL mode versus our snapshot is an outstanding **prompt-design comparison limit**, not a renderer failure. Both production builds pass and warn about large chunks; package/build sizes are not a visual-quality or latency winner.

## Versions, screenshots and reproduction

OpenUI react-lang/lang-core1.0.1, react-ui0.18.1, devtools0.3.0 (MIT); json-render core/react/shadcn0.21.1 (Apache-2.0); both final roots Zod4.3.6. Shared baseline: CopilotKit1.79.1, AG-UI client1.0.2, React19.2.4, AntD6.6.6, ECharts6.1.0, echarts-for-react3.0.6, Node24.18.0/Python3.12.3. Locks and installed-package metadata are committed. The new branches do not exercise their inherited unused A2UI dependencies, so simultaneous OpenUI+A2UI compatibility is not claimed.

Fresh screenshots in the assigned review folder show **Bob, revision2,18/20 values**, desktop1440×1000 and mobile390×844:

- `baseline-wide-desktop.png`, `baseline-wide-mobile.png` — existing reference.
- `library-openui-desktop.png`, `library-openui-mobile.png`, `library-openui-reordered.png`, `library-openui-evidence.png`.
- `library-json-render-desktop.png`, `library-json-render-mobile.png`, `library-json-render-reordered.png`, `library-json-render-evidence.png`.

The panels look alike because the same AntD/ECharts components render them; the reordered captures establish independent composition rather than a new visual design. Native OpenUI82/84 and shadcn36-widget appearance/accessibility were not exhaustively rendered. Full keyboard/screen-reader assessment and incomplete SVG contrast still need manual evaluation.

Each comparison/README.md has exact reproduction steps. `npm ci`, `npm test`, `npm run build`, `npm run fixtures`, `npm run test:domain`, `npm run test:browser` and `npm run capture` reproduce local checks. Runtime4111/4112 and preview5181/5182 share the fixed AG-UI Python emitter on8111. The canonical count ledger/script is in ui-openui; do not reset its exhausted budget. Source snapshots, hashes, elapsed count times, raw test outcomes and PNG manifests are retained. Build/script durations include tool overhead and are not a measured runtime ranking.

First-party references: [OpenUI source](https://github.com/thesysdev/openui), [built-in React UI](https://openui.com/docs/api-reference/react-ui), [CopilotKit slot integration](https://openui.com/docs/build-agents/copilotkit), [benchmark methodology](https://openui.com/docs/openui-lang/benchmarks), [json-render source/catalog](https://github.com/vercel-labs/json-render), [assistant-ui source/license and shell capabilities](https://github.com/assistant-ui/assistant-ui). assistant-ui remains an untested optional shell replacement; no Tambo or unrelated framework prototype was started.

## Handoff limits

This concludes the narrow library comparison. The recommendation retains the existing complementary3-library UI mix with compact JSON references; OpenUI/json-render are working, measured optional composition layers, not rejected as incompatible. A richer prebuilt catalog or larger composition task may change the tradeoff, but current evidence does not show enough token/visual benefit to justify changing the main plan. Equally tuned prompts, live Gemma generation success, native-library widget quality, real data/model answers, production authorization and durable memory remain untested and must stay explicit.

Cleanup complete: the owned Python8111, runtimes4111/4112 and previews5181/5182 were stopped, and all four owned named browser sessions were closed. Main application implementation still waits for plan review; no publishing occurred.
