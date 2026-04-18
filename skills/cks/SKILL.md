---
name: cks
description: Constitutional Knowledge System - unified command for search, add, and session extraction
category: knowledge
version: 1.0.0
status: stable
enforcement: advisory
triggers:
  - /cks
  - "knowledge search"
aliases:
  - /cks

suggest:
  - /search
  - /daemon
---

# /cks - Constitutional Knowledge System

## Purpose

Constitutional Knowledge System — unified command for searching, adding, and session extraction. Stores and retrieves project wisdom with FAISS vector search.

## Project Context

### Constitution / Constraints
- **Solo-dev constraints apply** (CLAUDE.md)
- **Privacy-first**: Local knowledge base, no external transmission
- **Evidence-based**: Actual project learnings, not generic advice
- **Instant results**: Pre-loaded daemon for <1s semantic search

### Technical Context
- **CLI**: `cks` (via installed package - verify with `pip show claude-cks`)
- **Entry types**: memory, pattern, code, knowledge, correction, insight, learning
- **Storage**: FAISS vector index for semantic search
- **Integration**: Unified with /search (chat history + web + semantic)

### Architecture Alignment
- Integrates with /search (unified intelligent search)
- Replaces: /cks-add, /learn, /ingest (now deprecated)

## Your Workflow

### Subcommands

**`/cks add`** - Add content to CKS with auto-detection
```bash
/cks add "Results: 32% reduction in latency"
/cks add --file pattern.md
/cks add --url https://example.com/article
```

**`/cks search`** - Search CKS (default behavior)
```bash
/cks "hook patterns"
/cks search "hybrid enforcement"
```

**`/cks session`** - Extract from current session
```bash
/cks session
```

**`/cks`** (no arguments) - Auto-extract lessons from current session
```bash
/cks                    # Extract and store lessons from current session
```

## Validation Rules

### Content Type Detection (for `/cks add`)

| Pattern | Detection | CKS Method |
|--------|-----------|------------|
| **pattern** | "Results:", "Anti-pattern:", "%" | `CKS.ingest_pattern()` |
| **memory** | Q&A format (What/How/Why/etc.) | `CKS.ingest_memory()` |
| **code** | "def ", "class ", "function " | `CKS.ingest_code()` |
| **document** | Default / .md/.txt/.rst files | Chunking via ingest_cli |

### Prohibited Actions
- Transmitting knowledge externally (privacy violation)
- Presenting results without relevance context
- Losing original query context

## Quick Examples

```bash
# Add content (auto-detects type)
/cks add "Hybrid enforcement pattern... Results: 32% reduction"

# Search CKS
/cks "hook patterns"
/cks search "hybrid approach"

# Extract from session
/cks session

# From file
/cks add --file optimization_summary.md

# From URL
/cks add --url https://example.com/article
```
