# Experiment decision rule

All candidate outcomes are pending until their raw evidence/report is available.
Do not score an unavailable dependency or credential as a factual-accuracy zero;
record the capability as untested/blocked and state what ran.

## Shared priority order

1. Required behavior: exact facts, complete scope, valid evidence, correction and
   type-rule propagation, correct private/shared visibility. A known violation
   fails that candidate's acceptance gate regardless of speed.
2. Reproducibility and recovery: same fixtures, replay/restart/idempotency, explicit
   unknown/error handling, stable snapshot and raw outputs.
3. Useful quality difference: evidence recall for paraphrases, multi-panel usability,
   recovery capabilities and supported user workflows.
4. Cost/latency/resource/operational tradeoffs, measured where possible and otherwise
   clearly described as judgments. Simplicity alone does not prove better answers.

| Pair | Raw outcome | Selection status |
|---|---|---|
| Direct AG-UI vs CopilotKit + AG-UI | Pending real UI/protocol experiment | Pending |
| SQL + FTS vs SQL + hybrid semantic retrieval | Pending retrieval and bounded model evaluation | Pending |
| Explicit workflow vs LangGraph + same scoped ledger | Pending state/recovery experiment | Pending |

Testing boundaries: replayed UI payloads prove renderer/protocol behavior, not model
reasoning. Fixed memory proposals prove storage/scope/recovery behavior, not natural
language extraction or summarizer quality. Live Gemma calls require an actual
successful response and usage receipt; provider failure is not a fake answer.
Small local samples support narrow descriptive conclusions, not universal rankings.

When quality ties, report the tie and identify the concrete integration/recovery
benefit used for the proposed choice. Preserve competitors on their branches until
the user reviews the action plan. Do not merge experiments into the main app yet.
