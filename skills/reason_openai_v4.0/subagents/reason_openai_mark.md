---
description: Quickly update the last reason_openai log entry with outcome calibration data.
allowed-tools: Bash(python:*)
---

# /reason_openai_mark

Update the latest `/reason_openai` log entry with outcome calibration data.

Usage:
```
/reason_openai_mark --acted-on yes --correct yes --outcome-quality 4 --biggest-miss "underestimated coordination cost" --time-to-action 15
```

All fields are optional — only specify what you want to update.

## Fields

| Field | Values | Description |
|-------|--------|-------------|
| `--acted-on` | `yes`, `no`, `true`, `false` | Did you act on the recommendation? |
| `--correct` | `yes`, `no`, `true`, `false` | Was it directionally correct? |
| `--outcome-quality` | `1`–`5` | How good was the outcome? |
| `--biggest-miss` | text | What did it miss or underestimate? |
| `--time-to-action` | minutes | How long until you acted? |
| `--review-notes` | text | Any other notes |

## Example

```
/reason_openai_mark --acted-on yes --correct yes --outcome-quality 4 --biggest-miss "underestimated migration risk" --time-to-action 20
```

## After updating, run:

```
/reason_openai_analyze
```

to see the updated calibration summary.
