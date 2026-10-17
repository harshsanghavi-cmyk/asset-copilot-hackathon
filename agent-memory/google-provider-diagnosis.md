# Google Gemma client diagnosis — bounded handoff

## Latest directive and settled result

The user subsequently required official LangChain ChatGoogleGenerativeAI integration in LangGraph and stopped custom HTTP/native probes. **All client/test ownership has transferred to the backend worker; its SDK replacement supersedes the HTTP implementation discussed below. No further client edits or model requests are authorized for this diagnosis worker.** The current SDK file/tests are backend-owned; this report does not claim their success or author their changes.

The final additional diagnostic was **call35**, native Google `models/gemma-4-31b-it:generateContent` with actual compact Q1 planner, systemInstruction + user contents, minimal thinking and maxOutputTokens768. It returned **HTTP500 INTERNAL in0.88s**; the safe server-timing header reported747ms, with no request ID returned. This bypassed OpenAI-compatible translation and still did not yield a plan. The same neutral-classification diagnostic was prepared but **not sent** because the shared ledger showed an active serving request. No neutral-classification outcome is claimed.

This worker made **seven** diagnostic requests total:24–29 and35, all settled. Three of the original ten-request allowance remain unused by this worker. Intervening serving/manual calls belong to other authorized callers and are not counted as diagnostic attempts. There is **no diagnostic request in flight by this worker**; do not infer current global serving state from that statement. The earlier29-total/zero-active figures below are historical checkpoint receipts, not the latest global count.

An offline cancellation reproduction also showed that cancelling GlobalLimiter.reserve during its rate-limit wait could leave its temporary test row marked reserved. That result was sent in handoff context; a proposed follow-up patch did **not** apply because the backend owner had already replaced the client under the new SDK directive. The backend owner should cover cancellation before HTTP start as well as HTTP/SDK timeout/cancellation. No runtime ledger row was modified by that reproduction.

The primary unresolved requirement is still a real schema-valid planner/maker and actual UI Q1. A useful generic greeting200 is not that acceptance result. The custom HTTP evidence neither proves the new SDK will fail nor establishes a successful root-cause fix. SDK implementation and the next authorized integration test belong to the backend/coordinator.

## Earlier HTTP diagnostic checkpoint (historical)

17 Oct 2026. **A realistic greeting succeeded, but actual data-planner generation remains blocked by Google HTTP500. Do not describe chat/Q1 as fixed.** Six additional diagnostic requests used the supplied root ignored.env GOOGLE_API_KEY, only gemma-4-31b-it and Google's compatible endpoint. No OpenRouter request, other model, service launch, dependency install, new session or fake fallback occurred in this task.

The backend owner explicitly handed over gemma.py and all live requests after the prior streaming Q1 probe settled500. Serving generation was disabled to prevent concurrent retries. Handoff ledger had23 generation attempts and no active requests; this task reserved24–29 through the same persistent GlobalLimiter at30RPM/2.2s, maximum100 total. Four of this task's ten permitted attempts remain unused. All six are settled; no further request is running.

## Actual new receipts

Authoritative sanitized metadata/usage are in runtime/model-requests.sqlite, calls24–29. No request text, key or Authorization header is persisted there. Elapsed measurements below came from the bounded diagnostic commands; failed500 requests returned no usage.

| Call | New test | Result |
|---|---|---|
|24| Useful natural oil-well greeting, JSON narrative + suggested question;440 content bytes, user role, max_tokens512, json_object, minimal thinking | **HTTP200**,23.35s;95 prompt +93 completion =188 reported tokens. Generated a substantive greeting describing inspection/maintenance/SOP evidence and asking which well/area to inspect. Not a literal echo. |
|25| Current planner/persona, real Q1 request and current provider catalog;5344 content bytes, user-only | **HTTP500**,25.52s, Google “Internal error encountered.” No parsed plan/answer |
|26| Same realistic planner with supported separate system/user roles;5294 content bytes | **HTTP500**,1.52s |
|27| Compact542-byte Q1 data planner, three permitted record operations, JSON mode, bounded768 output, minimal thinking | **HTTP500**,0.93s |
|28| Same compact request with only response_format removed | **HTTP500**,0.92s |
|29| Same compact request as27 with only vendor extra_body removed; JSON/max_tokens/temperature retained | **HTTP500**,0.91s |

Call24 proves useful model generation and JSON parsing can work with this credential/route. Its object is not the application's PlannerOutput greeting schema (`direct_response`), so it is **not** evidence that the UI greeting workflow passed. Calls25–29 fail at the provider HTTP layer before our JSON/schema parser. Compact542-byte failure rules out claiming that the full5344-byte prompt size alone explains the problem. Removing JSON mode or thinking configuration did not resolve this compact case. Earlier native500, compatible literal-JSON200, bad-envelope400, no-options timeout and OpenRouter429 remain historical observations, not additional requests by this task.

**Conclusion:** there is an observed input-dependent/intermittent Google internal-error boundary, not a demonstrated global outage or a proved single-parameter root cause. The client cannot turn those500 bodies into a real answer. Current evidence does not prove why Google fails these planner prompts. No schema/parser, SDK-install or alternative-model workaround is represented as a solution.

## Client changes and verification

Explicit ownership handoff allowed changes to [gemma.py](../backend/chains/gemma.py). Removed OPENROUTER_MODEL and all alternate host/model branches; a non-Google provider argument now fails before reservation/request. ModelReply, GlobalLimiter, configured and async generate interfaces remain compatible. Backend owner separately removed route selection from app/evaluator.

The Google request now uses one fixed model/host, bounded max_tokens, temperature0.1, response_format json_object and REST extra_body.google.thinking_config with minimal/include_thoughts=false. This is a documented bounded configuration that produced call24. **Restoring these options is not a proved universal fix**: the previous owner had deliberately removed them during failed isolation, and our larger/compact planners still fail with them. Several fields changed together before the successful greeting, so causality cannot be assigned to one field. Keep the report/ledger result boundary explicit.

[Dedicated offline tests](../backend/tests/test_google_client_diagnosis.py) passed **4/4** using httpx.MockTransport and temporary ledgers: Google-only refusal before request; fixed endpoint/model and correct REST vendor envelope; provider error/key redaction/status retention; streamed JSON assembly with reasoning stripped. Command: `backend/.venv/bin/python -B -m pytest backend/tests/test_google_client_diagnosis.py -q -p no:cacheprovider`. No real credential/provider call occurs in these tests. They prove client mechanics, not planner accuracy or Google reliability.

## Independent request/config inspection

- Endpoint is exactly Google's v1beta/openai/chat/completions with Bearer auth; httpx json serialization supplies application/json. This is direct REST, not an OpenAI SDK invocation with SDK-specific extra_body merging. No SDK/default-model fallback exists in this path.
- Diagnostic key was read privately from the root ignored.env GOOGLE_API_KEY, not another key variable. Parent process had no exported GOOGLE_API_KEY or HTTP/HTTPS/ALL_PROXY variables. Only presence was printed, never key bytes. A successful call24 establishes usable credentials for that request; it does not prove all server processes have identical environment precedence.
- Runtime create_app uses load_dotenv(override=False), so an externally exported key could precede the root value. No serving-key mismatch was established; backend owner should retain the explicitly selected credential source without dumping environment/key values.
- JSON parsing happens after successful HTTP200. Existing parse_json removes supported thinking tags/fences and requires one object. HTTP500 planner failures are not local parser/schema rejection. The fresh greeting was parsed successfully.
- Current diagnostics retain only sanitized model/roles/top-level request keys/content byte count and usage/error codes in the shared ledger. Provider errors are redacted before display. No request payload/private memory or complete response reasoning was copied into this report.

## Official source checks

Google lists gemma-4-31b-it as hosted and explicitly describes Gemma4 thinking as high/on or minimal/off, including native system instructions. Thus minimal is supported by Gemma-specific documentation, not assumed solely from Gemini examples. [Run Gemma with the Gemini API](https://ai.google.dev/gemma/docs/core/gemma_on_gemini_api).

The compatible API documentation shows the Google REST extension nested under extra_body.google, with JSON output controls and chat-message roles. SDK extra_body arguments and the serialized REST body must be distinguished; top-level google is not the documented REST envelope. This general compatibility documentation alone does not establish every Gemma parameter's reliability or strict JSON-schema enforcement. [Google OpenAI compatibility](https://ai.google.dev/gemini-api/docs/openai).

Gemma4's prompt-formatting documentation includes a system role and notes that thinking behavior can still need careful handling. We tested role separation rather than assume an older Gemma system-role limitation; it still returned500. [Gemma4 prompt formatting](https://ai.google.dev/gemma/docs/core/prompt-formatting-gemma4). Sources read17Oct2026; no model substitution follows from their examples of other models.

## Handoff / next action

Client/policy and four offline tests are reviewable; realistic data Q1 remains **NO GO**. Hand exclusive client/live-call ownership back to coordinator/backend with29 shared generation attempts, zero active, six of ten diagnostic attempts used. Backend may reload the Google-only client while keeping generation paused until coordinator chooses a bounded next test. Do not restart an unmetered probe loop or silently reopen OpenRouter.

If a later supported request succeeds, validate the actual PlannerOutput/greeting schema, then one real provider→query→maker envelope and UI Q1 before enabling ordinary retries. The natural greeting's different schema can be adapted by the backend owner, but must not be called a data answer. If the provider remains500, show the genuine blocked state and preserve deterministic results/receipts; no sample answer can substitute for a live success.
