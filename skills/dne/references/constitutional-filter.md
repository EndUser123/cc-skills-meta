# Constitutional Filter Reference

## Prohibited Patterns (Auto-Filter)

Before suggesting any action item, check against these prohibited patterns:

| Pattern | Filter Because | Alternative |
|---------|---------------|-------------|
| `lock ordering` | Enterprise bloat | Use single RLock per object |
| `continuous monitoring` | Background service prohibited | Use on-demand `/health` |
| `real-time metrics` | Background service prohibited | Use query-based metrics |
| `self-healing` | Autonomous execution prohibited | Manual fix with approval |
| `autonomous execution` | Autonomous execution prohibited | Step-by-step with confirmation |
| `enterprise-grade` | Enterprise pattern prohibited | Use simple solution |
| `scalability requirement` | Enterprise pattern prohibited | Optimize when needed |
| `team approval` | Consensus process prohibited | Singular dev decides |

## Python Filter Integration

```python
# Import the constitutional filter
from src.core.solo_dev_constitutional_filter import SoloDevConstitutionalFilter

filter_obj = SoloDevConstitutionalFilter()

# Check before suggesting
result = filter_obj.check_action_item(action)
if result.violates_constitution:
    # Don't suggest this action
    continue

# Or filter an entire list
filtered_actions = filter_obj.filter_action_items(action_items)
```

## Required Filter Step

**Before generating action items, ALWAYS run:**

1. Generate candidate action items
2. Filter with `SoloDevConstitionalFilter`
3. Only include compliant actions in output
