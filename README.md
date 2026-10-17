# Asset Intelligence Copilot

Local hackathon app: React/CopilotKit/AG-UI frontend, FastAPI/LangGraph backend, Google AI Studio Gemini 3.5 Flash Lite (`gemini-3.5-flash-lite`) through ChatGoogleGenerativeAI, and a replaceable SQLite/FTS retrieval provider.

## Run locally

1. Install Python3.11+, uv and Node/npm. Acquire the pinned dataset with `bash scripts/clone-dataset.sh`.
2. Copy `.env.example` to the ignored root `.env` and keep its final-dataset settings. Put your Google AI Studio key in the ignored root `.env` as `GOOGLE_API_KEY=...`. Never put a key in frontend code.
3. From the project root: `uv sync --project backend` then `uv run --project backend python -m backend` (API8000).
4. In `frontend/`: `npm ci` then `npm run runtime` (local CopilotKit runtime4190).
5. In another terminal in `frontend/`: `npm run build` then `npm run preview -- --host 127.0.0.1 --port 5192`.
6. Open http://localhost:5192 and choose Connected workspace. Admin diagnostics: http://localhost:5192/admin.html.

Use the production preview while testing responses; the development server on5190 may reload during source edits. The developer launcher creates a local admin capability file under ignored runtime/. The user selector is for this local challenge demo, not production authentication.

## Review and limitations

- [Current QA report](experiments/06-evaluation/QA_REPORT.md), [scoring](experiments/06-evaluation/SCORING.md), [review addendum](experiments/06-evaluation/QA_REVIEW_ADDENDUM.md), [latest verified fixes](experiments/06-evaluation/LATEST_VERIFICATION.md).
- [Executed WELL-0001 walkthrough](experiments/05-retrieval-viewer/WELL-0001-WALKTHROUGH.md).
- [Frontend implementation](agent-memory/ui-implementation.md), [backend implementation](agent-memory/backend-implementation.md), [retrieval implementation](agent-memory/retrieval-implementation.md).
- [Submission materials](submission/README.md).

The active dataset is the final 600-well snapshot in `dataset/test-data/dataset`, pinned at `009e2b596782150f420021f9472ab37e3a2953ee`, with reference date **15 Jan 2027**. Its 11 final scenarios include 21 conversational turns. The original 200-well sample and its 18-question QA remain archived regression evidence; they are not the active data or final acceptance results. Final scenario execution saves real answer envelopes to named database sessions visible in the connected UI. Provider availability, partial responses and remaining semantic failures stay explicit; no complete acceptance pass is claimed. Production is derived from corrected wellhead-minus-ambient temperature using the applicable supplied manual, not recorded status.

Raw source data is preserved. Runtime history, API credentials and generated databases are ignored by Git. Dataset acquisition is pinned and its upstream MIT license is retained. The source repository is published at https://github.com/harshsanghavi-cmyk/asset-copilot-hackathon. Hosting and hackathon portal submission remain manual.

## Final accepted delivery

All 11 final scenarios have run: 21 saved replies across 14 sessions, with 10 complete and 11 partial replies, and no fatal request errors. All 21 saved envelopes pass the frontend rendering contract. This is delivery validation, not a semantic accuracy score. See [final outputs](submission/ALL_11_RESULTS.md) and the [complete JSON bundle](submission/ui-json-results.zip). Refresh the connected UI, select the named user profile and open a `Final Q...` conversation.
