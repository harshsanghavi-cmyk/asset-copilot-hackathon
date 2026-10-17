# Coordinator findings

## Scope and ownership
Three high-effort GPT-6.1-sol sessions are being launched through Orca supervision.
Their requested/effective launch settings and dispatch IDs are in runtime/.
This phase produces research, skills, diagrams, contracts and a review plan only.

## OpenRouter verification — 17 Oct 2026
The public endpoint metadata is saved in openrouter-capabilities.json. It reports
response_format and tools/tool_choice, but does not list structured_outputs.
The model page says JSON output without schema enforcement. Do not claim strict
schema conformance from json_object; locally validate payloads and citations,
allow bounded formatting repair and fail transparently. No authenticated model
call has been made. Exact endpoint support is a phase-one compatibility check.
Sources:
- https://openrouter.ai/api/v1/models/google/gemma-4-31b-it:free/endpoints
- https://openrouter.ai/google/gemma-4-31b-it:free
- https://openrouter.ai/docs/guides/features/structured-outputs

## Submission evidence
The user screenshot shows required write-up and Drive video links, optional ZIP
<=150 MB. Repository/license remains a challenge requirement and belongs in the
write-up even though the screenshot has no dedicated repository URL field.
Submission templates are in submission/, with no invented results or publication.

## Image enhancement
The built-in image tool is available but exposes no explicit model selector.
An exact gpt-image-2 API call requires OPENAI_API_KEY, which is not configured.
The user explicitly selected the available built-in image tool instead. Do not
attribute a specific underlying model that the tool does not expose.
Editable Mermaid sources and source-grounded diagrams remain authoritative.

## Review artifact rule
The latest user instruction requires diagrams/ to contain final PNGs only.
All editable sources and briefs moved to agent-memory/diagram-sources/.
The overview PNG is conceptual. Detailed source diagrams define exact transport
edges and final flow; do not interpret decorative routing as an API contract.

## Integration questions for synthesis
- One versioned answer envelope with multiple blocks; data values reference exact
  tool datasets rather than being invented or retyped by the model.
- All blocks in an answer share a dataset and correction revision. A correction
  mid-query triggers a consistent refresh or explicit snapshot disclosure.
- User identity comes from the application boundary, not an LLM tool argument.
- Every aggregate returns coverage (matching/evaluated/unknown records) alongside
  units, date interval, source IDs and rule references.
- Summaries are derived projections; transcripts and correction provenance remain
  available for rebuilding. Typed selected-entity memory supports follow-ups.
- Background memory extraction/compaction should not hold the visible answer open;
  use a durable event/cursor and an explicit consistency boundary for next turns.
- End-to-end success, cross-user correction and unknown-data behavior precede
  decorative refinement in the implementation sequence.
