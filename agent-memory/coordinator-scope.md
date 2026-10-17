# Active coordinator file ownership

17 October 2026, urgent runtime switch. Root exclusively owns:

- backend/chains/gemma.py (compatibility module; active Google model becomes Gemini3.5FlashLite)
- backend/memory/budget.py
- backend/evaluate_live.py (archived sample evaluator)
- scripts/run-final-sessions.py and runtime batch execution
- root configuration/docs, final diagrams and submission document

The backend worker retains app.py, service.py, prompts, parsers, memory store and token_packing.py, but must not edit the coordinator-owned files above. The retrieval worker owns backend/retrieval and backend/ingestion; UI worker owns frontend except retrieval viewer. Luna owns evaluation reports only. This explicit narrow reassignment prevents the stalled worker connection from blocking the user-selected model switch. No worker process was stopped or assumed dead.
