# Coordinator second-pass review

The user challenged premature recommendations and asked for cross-user shared
remembered knowledge. The initial reports already included a shared correction
ledger, but their overview emphasized private memory and did not make shared
semantic knowledge sufficiently explicit. This is a real communication/design gap.

## Changes required before final recommendation

1. Separate architectural axes. Application-owned fact authority is compatible
   with LangGraph orchestration; it is not a competing framework. Letta/Graphiti/
   Mem0/gbrain add different services or representations. Compare complete useful
   combinations, not unrelated components ranked as interchangeable products.
2. Shared semantic knowledge is broader than raw-data corrections: asset plans,
   equipment observations, type guidance and organization/team knowledge can be
   remembered and retrieved by other authorized users. Keep explicit scope,
   provenance, valid time, assertion/conflict status and revision.
3. Keep personal preferences and 'the wells we discussed' private. Saving a minimal
   domain fact does not publish the source user's whole conversation. A vague
   remember command needs only the missing scope/subject clarified, not a blanket
   confirmation flow for clear asset facts.
4. A general scoped-memory gateway must read both private continuity and applicable
   shared knowledge on every turn. Shared facts do not need to be copied into each
   user's profile. Structured corrections/rules always enter effective queries,
   independent of semantic ranking or whether they fit a prose summary.
5. Every proposed hybrid must pass cross-user read-after-write, conflicting claims,
   correction propagation, restart, overflow and mid-dashboard revision tests.
   No package capability should be represented as a tested app behavior.
6. The first framework decision must consider actual strengths: resumable graph
   state and bounded retries can justify LangGraph even for a small dataset.
   A graph memory index may improve relationships across prose, but may also
   introduce extraction/schema errors and asynchronous stale truth.

## Independent primary-source checks, 17 Oct 2026

- LangGraph distinguishes thread checkpoints and arbitrary long-term namespaces,
  including user/org profiles. This supports private and shared scopes, but
  authorization and domain correction semantics remain application policy.
  https://docs.langchain.com/oss/python/concepts/memory
- Letta legacy blocks can be shared, but concurrent whole-value replacements are
  last-write-wins. Use an authority layer/version checks rather than assuming a
  shared block preserves every correction.
  https://docs.letta.com/v1-sdk/memory/memory-blocks
- Current Letta shared repository APIs are a different Cloud SDK path, with commit
  versions and content-hash preconditions. Do not mix their contracts with legacy
  block examples or claim a local Cloud-free integration from those docs.
  https://docs.letta.com/agent-sdk/repositories
- Graphiti supports temporal relationships and OpenAI-compatible providers. Its
  README explicitly warns about structured extraction reliability and offers
  json_schema/json_object modes. Therefore Gemma compatibility requires a small
  extraction test, not an assumption from endpoint compatibility alone.
  https://github.com/getzep/graphiti
- Mem0 search requires carefully scoped filters; managed/OSS API capabilities differ.
  Private user filtering is not a complete design for shared organizational facts.
  https://docs.mem0.ai/core-concepts/memory-operations/search

The independent architecture-review session now challenges complete hybrid designs
and writes scenario walkthroughs and a weighted, explicitly judgement-based matrix.
The final plan will supersede earlier checkpoint recommendations where they differ.
