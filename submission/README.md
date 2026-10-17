# Submission artifacts

Primary live write-up: https://docs.google.com/document/d/1Q6hCoswobev7UAoJV3pSMTYVgnKjGN67p0f0ZgWzt3E/edit

Completed delivery: all 11 final scenarios, 21 replies, 14 sessions. The final accepted run uses Gemini 3.5 Flash Lite over the separate 600-well dataset, reference 15 Jan 2027. It delivered 10 complete replies and 11 partial replies, with zero fatal request errors. Delivery does not establish semantic accuracy; partial explanations remain visible.

- `asset-copilot-writeup.docx`: export of the updated live Google Doc; four original diagrams, all 11 questions and 21 saved JSON answers, no tables.
- `asset-copilot-writeup.pdf`: local PDF of the same architecture and final-result content. The JSON appendix includes all returned rows, so it is intentionally long.
- `ALL_11_RESULTS.md`: all questions and saved JSON in code blocks. Repeated evidence excerpts are omitted, with source handles retained.
- `ui-json-results.zip` and `results/all11/`: complete unchanged answer envelopes, including every evidence excerpt and generation status.
- `FINAL_RUN_STATUS.json`: final delivery counts.
- `diagrams/`: original images 10, 12, 13 and 14, unchanged.

Open http://localhost:5192, refresh, select the scenario's user profile and open a `Final Q...` conversation. The session/profile mapping is in `experiments/06-evaluation/final-sessions/all11-final-accepted/RESULTS.md`.

Earlier files in `results/q1-q7/` are historical drafts. Use `results/all11/` for submission.

Dataset acquisition is reproducible via `scripts/clone-dataset.sh`. Runtime databases, credentials and local browser state are excluded from Git. The supplied dataset profiles are prototype identities, not production authentication.
