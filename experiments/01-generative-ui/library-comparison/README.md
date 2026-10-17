# OSS library comparison — finished experiments

[Full measured report](REPORT.md) includes branch commits, exact versions, catalog counts, token-method caveats and reproduction.

**Recommendation:** retain wide CopilotKit + Ant Design + ECharts with compact reference JSON. Both OpenUI and json-render work as optional independently composed catalog layers; the same actual visual components look alike. Only fixed serialization tokens were measured with Gemma, not generation reliability.

| Actual desktop | Mobile |
|---|---|
| [Existing baseline](baseline-wide-desktop.png) | [Baseline](baseline-wide-mobile.png) |
| [OpenUI + same components](library-openui-desktop.png) | [OpenUI](library-openui-mobile.png) |
| [json-render + same components](library-json-render-desktop.png) | [json-render](library-json-render-mobile.png) |

Composition proofs: [OpenUI reordered](library-openui-reordered.png), [json-render reordered](library-json-render-reordered.png). Evidence drilldown: [OpenUI](library-openui-evidence.png), [json-render](library-json-render-evidence.png).

Matched output tokens: compact JSON161, OpenUI148, JSON-wrapped OpenUI173, json-render snapshot242. OpenUI saves about8% output here, not the vendor's different-benchmark maximum. Input/default-prompt counts are separately reported; json-render's default prompt describes JSONL patches and is **not a fair optimized snapshot total**. Do not rank libraries by that default overhead or infer actual model reliability.

Actual native model-visible exports: OpenUI General82/Chat84, json-render shadcn36. These include helpers, and neither provides this whole evidence-bound analytic catalog out of the box. Exactly the same7 custom entries were exposed in both trials, including five useful panels and separate coordinated controls.

All8 local browser checks, type/build checks and scope/revision/ref guards pass. Final captures show no mobile document overflow and zero axe violations, with incomplete contrast/manual accessibility gaps retained. Main application remains untouched. Root owns final integration/plan approval.
