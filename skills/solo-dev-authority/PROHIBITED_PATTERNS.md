PROHIBITED PATTERNS - Detection Phrases

## Immediate Rejection Phrases

When you see these phrases, STOP and evaluate:

### Background Service Indicators (Always-On - PROHIBITED)
- continuous monitoring (without idle timeout)
- real-time metrics collection (without idle timeout)
- background health check (without idle timeout)
- periodic compliance scan
- always-on validation
- health status table (without idle timeout)
- compliance tracking
- ecosystem status

**ALLOWED: Background services with idle timeout auto-shutdown**
- Daemon starts on demand, shuts down after N seconds idle
- Example: `--idle-timeout 900` (auto-shutdown after 15 minutes)
- Pattern exists in: `__csf/src/daemons/unified_semantic_daemon.py:1250-1296"

### Autonomous Execution Indicators
- self-healing system
- automatic remediation
- autonomous execution
- background repair
- auto-fix
- self-correcting

### Consensus Pattern Indicators
- requires team approval
- stakeholder consensus required
- cross-team coordination needed
- organizational governance
- mandatory review process
- approval workflow
- peer review required

### Deployment Confusion Indicators
- deploy to production
- staging environment
- rollout plan
- feature flags
- production readiness check
- configuration file for features

## For Each Detection

1. STOP generation
2. Identify the specific prohibited pattern
3. Ask if on-demand alternative is acceptable
4. If user confirms, proceed with alternative
5. If user objects, explain constitutional constraint