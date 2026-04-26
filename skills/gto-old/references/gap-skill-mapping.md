# Gap-to-Skill Mapping (Layer 2)

GTO includes an intelligent skill recommendation system that analyzes gaps and suggests relevant skills.

## Components

- `lib/skill_registry_bridge.py` - Loads skill metadata from registry with fallback catalog
- `lib/gap_skill_mapper.py` - Maps gap types to skill categories using `GAP_TYPE_TO_CATEGORIES`
- `lib/skill_coverage_detector.py` - Gap-aware recommendations for RSN output

## How It Works

1. When gaps are found, GTO analyzes each gap's type (session_outcome, git_dirty, etc.)
2. Gap types are mapped to relevant skill categories (vcs, session, skill_coverage, etc.)
3. Skills are matched based on category, domain, and trigger keywords
4. Recommendations include skill descriptions and rationale

## Gap Type to Skill Category Mapping

| Gap Type | Categories | Example Skills |
|----------|------------|----------------|
| git_dirty, uncommitted | vcs, git | /git, /push |
| session_outcome | session | (from chat transcript analysis) |
| skill_coverage_gap | skill_coverage | (from skill coverage log) |

## LLM Context Injection

When generating recommendations, GTO injects skill context into the RSN output so the LLM understands what skills are available and what they do. This enables context-aware suggestions rather than static recommendations.
