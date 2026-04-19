# Orchestrator API Reference

## Phase 1 API (Core Orchestration)

```python
from orchestrator import (
    invoke_skill, get_suggestions, get_audit_trail,
    get_stats, get_skill_info, validate_workflow, suggest_workflow
)

# Simple invocation
result = invoke_skill("/nse", {"query": "what's next?"})

# Get suggestions for a skill
next_skills = get_suggestions("/nse")

# Get workflow statistics
stats = get_stats()

# Get comprehensive skill info
info = get_skill_info("/nse")

# Validate a workflow
validation = validate_workflow(["/analyze", "/nse", "/design"])

# Suggest possible workflows
workflows = suggest_workflow("/nse", max_depth=3)
```

## Phase 2 API (Quality Pipeline)

```python
from orchestrator import master_orchestrator

# Get all quality skills by category
quality_skills = master_orchestrator.get_quality_skills()
# Returns: {'testing': ['/t', '/qa', ...], 'validation': [...], ...}

# Get recommended quality workflow
workflow = master_orchestrator.get_recommended_quality_workflow('standard')
# Returns: ['/t', '/comply', '/qa']

# Validate quality workflow
validation = master_orchestrator.validate_quality_workflow(['/t', '/qa'])
# Returns validation result with issues and recommendations

# Get quality pipeline summary
summary = master_orchestrator.get_quality_pipeline_summary()

# Record quality metrics
master_orchestrator.record_quality_metrics('/t', {
    'tests_passed': 42,
    'tests_failed': 3,
    'coverage_percent': 85.5,
    'issues_found': 7
})

# Get quality metrics
metrics = master_orchestrator.get_quality_metrics('/t')
all_metrics = master_orchestrator.get_quality_metrics()  # All skills

# Get next quality skills
next_skills = master_orchestrator.get_next_quality_skills('/t')
# Returns: ['/validate_spec', '/comply', '/qa']

# Check if skill is quality skill
is_quality = master_orchestrator.get_skill_info('/t')['is_quality_skill']
# Returns: True

# Get quality category
category = master_orchestrator.get_skill_info('/t')['quality_category']
# Returns: 'testing'
```
