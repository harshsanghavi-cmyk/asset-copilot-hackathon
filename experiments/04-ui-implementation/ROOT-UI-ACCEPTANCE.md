# Final chat controls: independent acceptance

Coordinator browser review of the served app at http://localhost:5192, 17 October 2026. This report distinguishes the real saved-data rendering checks from live model generation.

## Verified before the controls update

- The saved 200-asset fleet answer renders its table and map side by side on desktop. The latest saved four-panel answer renders in a two-column grid. The explicit single-row layout remains a horizontal row.
- At 390px viewport width, panels stack with no document-level horizontal overflow. Main answer and user text are 16px.
- Valid inline citations render as numbered source buttons. Raw bracketed memory/result identifiers and the generic compliance warning wall are absent from the normal conversation.
- Both historical all-empty failed answers display a single empty state rather than six or seven repeated empty panels.

Evidence: `root-grid-readable-desktop.png`, `root-grid-readable-mobile.png`, and `root-grid-before-controls.png` in this directory. The incorrect historical four-well narrative remains historical model output; visual cleanup does not establish that its facts or scope are correct.

## Acceptance still to execute after deployment

1. Edit a user message, cancel without changing history, then submit an edit into a distinct conversation branch. Confirm the original conversation is intact after reload.
2. Regenerate an answer from its associated user message; confirm that the selected turn, rather than the latest unrelated question, is retried. Failed/partial continuation must preserve successful prior stages and committed memory receipts.
3. Complete a real answer and verify a separate Gemma suggestion request produces clickable question pills. Inspect its input construction to confirm it receives only the question, displayed answer and visible dialogue. Reading old history must not start new generation.
4. Verify disabled controls during active work, error/cooldown behavior, profile/session switching, keyboard access, and narrow-screen layout.

No additional model generation was used for the pre-update browser review.
