---
name: gemma-only-runtime
description: Maintain the Asset Copilot's exclusive Gemma model policy, direct Google/OpenRouter provider configuration, JSON validation and shared request budget. Use when changing model clients, extraction, retrieval assistance, summaries or output parsers in this project.
---

# Gemma-only runtime

Read `../../AGENTS.md`, `../../agent-memory/model-policy.md` and the current provider
verification artifact before changing a client. The user permits Gemma4 31B Instruct
only in every copilot layer. Do not add MiniLM, another embedding/reranking model,
a different Gemma variant, or a fallback LLM. GPT-6.1-sol development workers are
separate from runtime model selection.

Current temporary provider: Google AI Studio, model `gemma-4-31b-it`, base URL
`https://generativelanguage.googleapis.com/v1beta/openai/`. The user expressly
supplied this provider key. Read GOOGLE_API_KEY from ignored local configuration;
never echo, log, commit, place in prompts or send it to another provider.
The older OpenRouter slug is `google/gemma-4-31b-it:free`; changing providers must
preserve model identity and follow the user's current choice.

The verified compatible JSON request used `response_format.type=json_object`
and Google's extra_body.google.thinking_config with thinking_level=minimal and
include_thoughts=false. Plain generation and clean JSON succeeded; native
GenerateContent failed HTTP500 during this check. This is a narrow observed
compatibility result, not a universal guarantee. See
`../../agent-memory/google-gemma-verification.json` for sanitized receipts.

Count requests globally across planner, answering, extraction, memory and repair.
Respect the user-reported maximum30RPM; serialize experiment requests with at
least2.2seconds between starts and retain an attempt counter across restarts.
On429/5xx, obey retry hints and bounded backoff. Never hide failure with a model
substitution or retry storm. Preserve completed deterministic results as partial
answers when model generation is unavailable.

Keep prompts as Markdown referenced by YAML input:/prompt: configuration, chains
under backend/chains and validation/repair under backend/output_parsers. Validate
JSON, schema, IDs, evidence and exact values locally. Do not render raw reasoning
or partial model JSON as an operator answer. Allow at most one bounded formatting
repair without changing tool-calculated facts or replaying a committed write.

Use deterministic splitting, SQL, FTS/BM25 and explicit joins freely. Gemma can
propose query expansion or source-backed extractions, but its success must be
measured separately from retrieval mechanics. Preserve originals, source spans,
unknowns and full-population numerical coverage. Historical other-model experiment
scores are ineligible under this policy, regardless of their measured gains.
