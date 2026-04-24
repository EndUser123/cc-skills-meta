---
description: Minimal .mcp.json template for /reason_openai MCP servers.
allowed-tools: Bash(python:*)
---

# `.mcp.json` Template for `/reason_openai`

Place this at your repo root (or `~/.claude/` for user-scope servers).

## Full template

```json
{
  "mcpServers": {
    "github": {
      "command": "${GITHUB_MCP_COMMAND:-npx}",
      "args": [
        "-y",
        "@YOUR_GITHUB_MCP_PACKAGE"
      ],
      "env": {
        "GITHUB_TOKEN": "${GITHUB_TOKEN}"
      }
    },
    "docs": {
      "command": "${DOCS_MCP_COMMAND:-npx}",
      "args": [
        "-y",
        "@YOUR_DOCS_MCP_PACKAGE"
      ],
      "env": {
        "DOCS_API_KEY": "${DOCS_API_KEY:-}"
      }
    },
    "browser": {
      "command": "${BROWSER_MCP_COMMAND:-npx}",
      "args": [
        "-y",
        "@YOUR_BROWSER_MCP_PACKAGE"
      ],
      "env": {}
    },
    "database": {
      "command": "${DB_MCP_COMMAND:-npx}",
      "args": [
        "-y",
        "@YOUR_DB_MCP_PACKAGE"
      ],
      "env": {
        "DATABASE_URL": "${DATABASE_URL}"
      }
    },
    "monitoring": {
      "command": "${MONITORING_MCP_COMMAND:-npx}",
      "args": [
        "-y",
        "@YOUR_MONITORING_MCP_PACKAGE"
      ],
      "env": {
        "MONITORING_API_KEY": "${MONITORING_API_KEY:-}"
      }
    },
    "task-tracker": {
      "command": "${TASK_MCP_COMMAND:-npx}",
      "args": [
        "-y",
        "@YOUR_TASK_MCP_PACKAGE"
      ],
      "env": {
        "TASK_API_KEY": "${TASK_API_KEY:-}"
      }
    }
  }
}
```

## Windows note

On native Windows, wrap `npx` with `cmd /c` to avoid "Connection closed" errors:

```json
{
  "github": {
    "command": "cmd /c npx",
    "args": ["-y", "@YOUR_GITHUB_MCP_PACKAGE"],
    "env": { "GITHUB_TOKEN": "${GITHUB_TOKEN}" }
  }
}
```

## Scope guidance

| Server | Recommended scope | Why |
|--------|------------------|-----|
| github, docs, browser | **user** or **project** | Broadly useful across repos |
| database, monitoring | **project** only | Environment-specific credentials |
| task-tracker | **project** only | Team-specific workflow |

## Setup commands (CLI alternative to hand-editing)

```bash
# User-scope (available everywhere)
claude mcp add github --scope user -- npx -y @YOUR_GITHUB_MCP_PACKAGE
claude mcp add docs --scope user -- npx -y @YOUR_DOCS_MCP_PACKAGE
claude mcp add browser --scope user -- npx -y @YOUR_BROWSER_MCP_PACKAGE

# Project-scope (version-controlled with repo)
claude mcp add database --scope project -- npx -y @YOUR_DB_MCP_PACKAGE
claude mcp add monitoring --scope project -- npx -y @YOUR_MONITORING_MCP_PACKAGE
claude mcp add task-tracker --scope project -- npx -y @YOUR_TASK_MCP_PACKAGE
```

## Verify MCP status inside Claude Code

```bash
claude mcp list
/mcp
```

## MCP prompts as slash commands

After connecting, check for exposed prompts:

```
/mcp__github__pr-review
/mcp__github__issue-summary
/mcp__docs__api-lookup
/mcp__monitoring__incident-triage
```

These become reusable tool-backed workflows inside `/reason_openai`.