# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [5.15.2] - 2026-03-18

### Changed
- **Expanded asset generation tool table** - Added alternative tools for each asset type
  - Banner: OpenRouter, Midjourney, Stable Diffusion, PIL (manual)
  - Architecture overview: NotebookLM, DALL-E 3, Mermaid, PlantUML, Graphviz
  - Flowcharts: Mermaid, PlantUML, Graphviz DOT, draw.io
  - Explainer video: NotebookLM, Luma Dream Machine, Runway Gen-3, HeyGen
  - Slide deck: NotebookLM, Marp, Pandoc, PowerPoint
  - Tool selection notes added for choosing best option per use case

## [5.15.1] - 2026-03-18

### Added
- **Banner validation script** - `validate_banner.py` for automated banner quality checking
  - Basic property validation (dimensions, file size, corruption check)
  - Z.ai Vision API integration for quality scoring (1-10 scale)
  - Text readability, professionalism, and visual appeal assessment
  - Structured output with issues and recommendations
  - `--fail-on-issues` flag for CI/CD integration

### Changed
- Updated PHASE 4.7 (Media Generation) documentation with banner validation workflow
- Added quality verification criteria for banner assets (Excellent 8-10, Good 6-7, Needs improvement <6)

## [5.15.0] - 2026-03-18

### Changed
- **Phase renumbering**: Reorganized phases into logical sequential order (0-15)
  - Eliminated fractional phase numbers (1.5, 1.6, 1.7, 4.5, 4.6, 4.7)
  - Moved Quality Scanning to PHASE 7.5 (within Validate phase)
  - Media Generation now PHASE 9 (between Code Review and Portfolio Polish)
  - GitHub Publication now PHASE 11 (was PHASE 6)
  - Repository Finalization now PHASE 12 (was PHASE 7)
  - All subsequent phases renumbered sequentially
- **PHASE 9 auto-run logic fixed**: Now runs when assets are MISSING (not when README lacks images)
  - Auto-run triggers: No assets exist in `assets/` directories OR README.md exists
  - Auto-skip triggers: Assets already exist OR user opts out with `--skip media`
- Updated version to 5.15.0

## [5.12.0] - 2026-03-18

### Added
- **PHASE 6: GitHub Publication** - Complete end-to-end GitHub workflow
  - PHASE 6.1: Monorepo extraction (subtree split or fresh init methods)
  - PHASE 6.2: GitHub repository creation via GitHub CLI (gh)
  - PHASE 6.3: Author/license automation from git config
  - PHASE 6.4: Package-specific validation rules
  - PHASE 6.5: Post-publication verification
- Windows-compatible Python scripts for GitHub publication:
  - `extract_from_monorepo.py` - Monorepo extraction with history preservation
  - `create_github_repo.py` - GitHub repo creation with manual fallback
- `package_validations.json` - Target-specific validation rules for search-research, skill-guard, loop-core, and generic packages
- Junction setup at `.claude/skills/gitready/` for automatic skill file syncing

### Changed
- Renumbered PHASE 6 (Cleanup) → PHASE 7
- Renumbered PHASE 7 (Git Ready + Recruiter) → PHASE 8
- Updated workflow_steps frontmatter to include new PHASE 6

## [5.11.0] - 2026-03-18

### Added
- Initial PHASE 6 implementation planning and structure
- Package validation framework design
- Monorepo extraction strategy documentation

## [5.5.3] - 2026-03-10

### Added
- GitHub video embedding instructions for inline video playback
- Template includes user-images CDN upload guide for both explainer video and podcast
- Clear step-by-step instructions for enabling embedded video via GitHub web editor
- Fallback badge links for repo-hosted videos (download required)

### Changed
- Corrected skill documentation to reflect GitHub DOES support embedded `<video>` tags
- Updated Media Assets section template with proper video embedding structure
- Removed incorrect claim that GitHub doesn't support video embedding

## [5.5.2] - 2026-03-10

### Added
- Explicit CI/CD workflow template in skill documentation
- Clear NO Codecov instruction to prevent external service uploads
- Local coverage reporting only (--cov-report=term)

### Changed
- Updated skill to prevent future Codecov integration confusion

## [5.5.1] - 2026-03-10

### Added
- Comprehensive "Three Deployment Models" documentation in README
- Decision guide table for choosing deployment model
- "Common Mistakes to Avoid" section
- Local development junction setup
- Git initialization and initial commit structure

### Changed
- Enhanced README with complete deployment documentation
- Improved developer onboarding experience

## [5.5.0] - 2026-03-10

### Added
- Initial Claude Code plugin structure
- Core module with version management
- Hook configuration framework
- Test suite with passing tests
- MIT License
- Comprehensive README documentation
- Three deployment models: SKILLS, HOOKS, PLUGINS

### Features
- Universal Package Creator & Portfolio Polisher
- Supports Claude skills, Python libraries, and Claude Code plugins
- Portfolio polish with badges, CI/CD, and media artifacts
- Brownfield conversion from Python libraries to plugins

## [5.4.0] and earlier

See previous skill documentation for historical changes.

[5.15.2]: https://github.com/EndUser123/gitready/compare/v5.15.1...v5.15.2
[5.15.1]: https://github.com/EndUser123/gitready/compare/v5.15.0...v5.15.1
[5.15.0]: https://github.com/EndUser123/gitready/compare/v5.14.0...v5.15.0
[5.14.0]: https://github.com/EndUser123/gitready/compare/v5.12.0...v5.14.0
[5.12.0]: https://github.com/EndUser123/gitready/compare/v5.11.0...v5.12.0
[5.11.0]: https://github.com/EndUser123/gitready/compare/v5.5.3...v5.11.0
[5.5.3]: https://github.com/EndUser123/gitready/compare/v5.5.2...v5.5.3
[5.5.2]: https://github.com/EndUser123/gitready/compare/v5.5.1...v5.5.2
[5.5.1]: https://github.com/EndUser123/gitready/compare/v5.5.0...v5.5.1
[5.5.0]: https://github.com/EndUser123/gitready/compare/v5.4.0...v5.5.0
