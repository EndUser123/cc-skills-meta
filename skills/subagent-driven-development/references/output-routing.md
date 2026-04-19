# Subagent Output Routing Reference

## Result Envelope

Every subagent writes detailed output to disk and returns only a small envelope to the orchestrator. See canonical spec: `.claude/skills/shared/result-envelope.md`.

```json
{
  "status": "done" | "blocked" | "retry",
  "artifact": "relative/path/to/output/file.ext",
  "summary": "≤3 short lines — no code, no diffs, no large analysis",
  "metrics": { "artifact_bytes": 4821, "files_read": 3 }
}
```

The orchestrator consumes only Result Envelopes plus selective reads of artifacts; it never inlines full artifact content into its own context.

## Output Routing Tiers

| Tier | Name | Contains | Access |
|------|------|----------|--------|
| 0 | Orchestrator Window | Envelopes, decisions, IDs, file paths, short summaries | Active LLM context |
| 1 | Artifact Store | Full analyses, diffs, logs, tool outputs, phase summaries | Read via path from envelope |
| 2 | History Archive | Old handoff chains, prior session histories | Explicit retrieve only |

Subagents write full results into Tier 1; return envelopes into Tier 0. Do not promote Tier 1 content into Tier 0 without summarization. Tier 2 is never loaded by default.

## Routing Rules

- **Phase boundaries = context resets** — use the handoff system between major phases. Start a fresh session; load only the phase summary file, not full conversation history.
- **Sequential by default** — tasks that produce large artifacts (full diffs, complete implementations, long analyses) are high-output and must run sequentially. Tasks that produce only metadata, verdicts, or short structured JSON are low-output and may run in parallel. When in doubt, treat a task as high-output.
- **Spike before high-output tasks** — when a task would produce a large artifact, the first sub-task is always: write type signatures, interfaces, and acceptance criteria only. Review before proceeding to implementation.
- **Targeted file reads** — instruct subagents to use `Grep` to locate sections first, then `Read` with `offset`/`limit`. When only part of a file is relevant, read only that part. If a full read is genuinely needed and the file is clearly large, write a summary artifact and return a pointer; do not inline the full content.
- **Pass task excerpts, not full plans** — brief each subagent with only the task block it needs, not the entire plan document.
