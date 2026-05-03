Set-Location 'P:\packages\.claude-marketplace\plugins\cc-skills-meta\skills\doc-compiler'
$env:DOCC_TARGET = 'P:\packages\.claude-marketplace\plugins\cc-skills-meta\skills\genius\SKILL.md'
python -m doc_compiler.runtime.orchestrator
