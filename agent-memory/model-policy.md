# Exclusive model policy — verified direct Google route

Only Gemma 4 31B Instruct may be used across the copilot pipeline. User authorized
Google AI Studio direct access temporarily, so the model identifier is
gemma-4-31b-it and base URL is https://generativelanguage.googleapis.com/v1beta/openai/.
The earlier OpenRouter identifier names the same chosen model; provider transport
has changed with explicit user authorization. GOOGLE_API_KEY is held only in the
ignored local .env. No credential value belongs in reports, prompts or commits.

Controlled verification (google-gemma-verification.json): model metadata and token
counting returned200; native generateContent returned500 twice; Google's compatible
chat endpoint returned200 and generated GEMMA_OK. The first response contained a
reasoning tag, so the final text was separated for checking. A subsequent JSON
request with thinking minimal/include_thoughts false returned clean parseable JSON
without reasoning markup. This proves a smoke test, not universal schema or task
accuracy. Keep local schema/evidence validation and bounded repair.

Global rate cap:30 requests/minute as supplied by the user, across all app layers.
Use one coordinator-approved live experiment at a time during research; serialize
requests with at least2.2seconds between starts. No alternative models/embeddings.
Deterministic parsing, splitting, SQL, FTS/BM25 and exact graph joins are allowed.
Historical MiniLM results are INELIGIBLE for integration and do not define our
selected retrieval architecture. Gemma query expansion/extraction may assist the
deterministic retrieval layer, but must earn adoption through matched evidence.

Code-development workers remain GPT-6.1-sol as requested; they are not copilot
runtime models. Main implementation still waits for final-plan review.

## Latest user override

Google AI Studio ONLY for active inference, model gemma-4-31b-it. OpenRouter is no longer authorized as an active route or fallback; earlier probes are historical. Fix the Google integration without switching models or exposing credentials.

## Latest selected model: Gemma 4 26B

The user explicitly authorizes replacing Gemma4 31B with Gemma4 26B. Active runtime model is now `gemma-4-26b-a4b-it` through Google AI Studio using ChatGoogleGenerativeAI. This supersedes previous31B-only restrictions in every runtime layer. No OpenRouter or automatic model fallback. Keep31B test receipts as historical evidence. Shared30RPM limiter and explicit token accounting remain.
