Set-Location 'P:\packages\.claude-marketplace\plugins\cc-skills-meta\skills\doc-compiler'
$env:DOCC_TARGET = 'P:\packages\.claude-marketplace\plugins\cc-skills-meta\skills\genius\SKILL.md'
# Skip F, I, J, K (LangGraph gates) and run only deterministic stages
& python runtime/stage_a_source_extractor.py
& python runtime/stage_b_doc_model_builder.py
& python runtime/stage_c_diagram_strategy_router.py
& python runtime/stage_d_guide_loader.py
& python runtime/stage_e_diagram_generator.py
& python runtime/stage_g_artifact_plan_builder.py
& python runtime/stage_h_template_html_emitter.py
Write-Output "Deterministic stages complete"
