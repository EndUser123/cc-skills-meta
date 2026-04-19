# Orchestrator CLI Reference

## Phase 1 Commands

```bash
# Show suggestions for a skill
python orchestrator.py --suggest <skill>

# Show comprehensive skill info
python orchestrator.py --info <skill>

# Validate a workflow sequence
python orchestrator.py --validate <skill1,skill2,...>

# Show workflow statistics
python orchestrator.py --stats

# Show all skill relationships
python orchestrator.py --graph
```

## Phase 2 Commands (via Python)

```python
# From Python CLI
python -c "from orchestrator import master_orchestrator; print(master_orchestrator.get_recommended_quality_workflow('standard'))"

# Show quality skills by category
python -c "from orchestrator import master_orchestrator; import json; print(json.dumps(master_orchestrator.get_quality_skills(), indent=2))"

# Validate quality workflow
python -c "from orchestrator import master_orchestrator; import json; print(json.dumps(master_orchestrator.validate_quality_workflow(['/t', '/qa']), indent=2))"
```
