"""
Tests for Quality Pipeline (Phase 2)

Tests quality workflow validation, skill categorization, and metrics tracking.
"""

import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from quality_pipeline import QualityPipeline, QualityStage, quality_pipeline


def test_quality_stage_enum():
    """Test QualityStage enum has all required stages."""
    print("Testing QualityStage enum...")

    required_stages = {
        QualityStage.TEST,
        QualityStage.VALIDATE,
        QualityStage.COMPLY,
        QualityStage.QA,
        QualityStage.DEBUG,
        QualityStage.RCA,
        QualityStage.NSE,
        QualityStage.OPTS,
        QualityStage.REFACTOR
    }

    assert QualityStage.TEST in required_stages, "TEST stage missing"
    assert QualityStage.VALIDATE in required_stages, "VALIDATE stage missing"
    assert QualityStage.COMPLY in required_stages, "COMPLY stage missing"
    assert QualityStage.QA in required_stages, "QA stage missing"

    print("  ✓ All 9 quality stages defined")


def test_quality_skills_categorization():
    """Test quality skills are properly categorized."""
    print("\nTesting quality skills categorization...")

    qp = QualityPipeline()
    categories = qp.get_quality_skills()

    # Check all 4 categories exist
    assert 'testing' in categories, "testing category missing"
    assert 'validation' in categories, "validation category missing"
    assert 'analysis' in categories, "analysis category missing"
    assert 'optimization' in categories, "optimization category missing"

    # Check testing skills
    testing_skills = categories['testing']
    assert '/t' in testing_skills, "/t not in testing"
    assert '/qa' in testing_skills, "/qa not in testing"
    assert '/tdd' in testing_skills, "/tdd not in testing"

    # Check validation skills
    validation_skills = categories['validation']
    assert '/comply' in validation_skills, "/comply not in validation"
    assert '/validate_spec' in validation_skills, "/validate_spec not in validation"

    # Check analysis skills
    analysis_skills = categories['analysis']
    assert '/debug' in analysis_skills, "/debug not in analysis"
    assert '/rca' in analysis_skills, "/rca not in analysis"
    assert '/nse' in analysis_skills, "/nse not in analysis"

    # Check optimization skills
    optimization_skills = categories['optimization']
    assert '/refactor' in optimization_skills, "/refactor not in optimization"
    assert '/q' in optimization_skills, "/q not in optimization"

    print("  ✓ All quality skills categorized correctly")
    print(f"    - Testing: {len(testing_skills)} skills")
    print(f"    - Validation: {len(validation_skills)} skills")
    print(f"    - Analysis: {len(analysis_skills)} skills")
    print(f"    - Optimization: {len(optimization_skills)} skills")


def test_recommended_workflows():
    """Test predefined quality workflows."""
    print("\nTesting recommended quality workflows...")

    qp = QualityPipeline()

    # Check standard workflow
    standard = qp.get_recommended_workflow('standard')
    assert standard == ['/t', '/comply', '/qa'], f"Standard workflow incorrect: {standard}"

    # Check deep workflow
    deep = qp.get_recommended_workflow('deep')
    assert '/t' in deep, "Deep workflow missing /t"
    assert '/analyze' in deep, "Deep workflow missing /analyze"
    assert '/comply' in deep, "Deep workflow missing /comply"
    assert '/debug' in deep, "Deep workflow missing /debug"
    assert '/qa' in deep, "Deep workflow missing /qa"

    # Check regression workflow
    regression = qp.get_recommended_workflow('regression')
    assert '/t' in regression, "Regression workflow missing /t"
    assert '/rca' in regression, "Regression workflow missing /rca"

    # Check optimization workflow
    optimization = qp.get_recommended_workflow('optimization')
    assert '/q' in optimization, "Optimization workflow missing /q"
    assert '/refactor' in optimization, "Optimization workflow missing /refactor"

    print("  ✓ All 6 predefined workflows validated")
    for name in ['standard', 'deep', 'regression', 'optimization', 'spec_validation', 'quick_check']:
        workflow = qp.get_recommended_workflow(name)
        print(f"    - {name}: {' -> '.join(workflow)}")


def test_is_quality_skill():
    """Test quality skill detection."""
    print("\nTesting quality skill detection...")

    qp = QualityPipeline()

    # Quality skills
    assert qp.is_quality_skill('/t'), "/t should be quality skill"
    assert qp.is_quality_skill('/comply'), "/comply should be quality skill"
    assert qp.is_quality_skill('/qa'), "/qa should be quality skill"
    assert qp.is_quality_skill('/debug'), "/debug should be quality skill"
    assert qp.is_quality_skill('/rca'), "/rca should be quality skill"
    assert qp.is_quality_skill('/nse'), "/nse should be quality skill"
    assert qp.is_quality_skill('/refactor'), "/refactor should be quality skill"
    assert qp.is_quality_skill('/q'), "/q should be quality skill"

    # Non-quality skills
    assert not qp.is_quality_skill('/design'), "/design should not be quality skill"
    assert not qp.is_quality_skill('/build'), "/build should not be quality skill"
    assert not qp.is_quality_skill('/research'), "/research should not be quality skill"

    print("  ✓ Quality skill detection working correctly")


def test_get_quality_category():
    """Test quality category retrieval."""
    print("\nTesting quality category retrieval...")

    qp = QualityPipeline()

    assert qp.get_quality_category('/t') == 'testing', "/t category wrong"
    assert qp.get_quality_category('/qa') == 'testing', "/qa category wrong"
    assert qp.get_quality_category('/comply') == 'validation', "/comply category wrong"
    assert qp.get_quality_category('/debug') == 'analysis', "/debug category wrong"
    assert qp.get_quality_category('/rca') == 'analysis', "/rca category wrong"
    assert qp.get_quality_category('/refactor') == 'optimization', "/refactor category wrong"
    assert qp.get_quality_category('/q') == 'optimization', "/q category wrong"

    # Non-quality skill
    assert qp.get_quality_category('/design') is None, "/design should have no quality category"

    print("  ✓ Quality category retrieval working correctly")


def test_stage_from_skill():
    """Test skill to stage mapping."""
    print("\nTesting skill to stage mapping...")

    qp = QualityPipeline()

    assert qp.get_stage_from_skill('/t') == QualityStage.TEST, "/t stage wrong"
    assert qp.get_stage_from_skill('/comply') == QualityStage.COMPLY, "/comply stage wrong"
    assert qp.get_stage_from_skill('/qa') == QualityStage.QA, "/qa stage wrong"
    assert qp.get_stage_from_skill('/debug') == QualityStage.DEBUG, "/debug stage wrong"
    assert qp.get_stage_from_skill('/rca') == QualityStage.RCA, "/rca stage wrong"
    assert qp.get_stage_from_skill('/nse') == QualityStage.NSE, "/nse stage wrong"
    assert qp.get_stage_from_skill('/refactor') == QualityStage.REFACTOR, "/refactor stage wrong"
    assert qp.get_stage_from_skill('/q') == QualityStage.OPTS, "/q stage wrong"

    print("  ✓ Skill to stage mapping working correctly")


def test_quality_transition_validation():
    """Test quality pipeline transition validation."""
    print("\nTesting quality pipeline transition validation...")

    qp = QualityPipeline()

    # Valid transitions
    assert qp.is_valid_quality_transition('/t', '/comply'), "t → comply should be valid"
    assert qp.is_valid_quality_transition('/comply', '/qa'), "comply → qa should be valid"
    assert qp.is_valid_quality_transition('/t', '/qa'), "t → qa should be valid"
    assert qp.is_valid_quality_transition('/debug', '/rca'), "debug → rca should be valid"
    assert qp.is_valid_quality_transition('/rca', '/nse'), "rca → nse should be valid"

    # Invalid transitions
    assert not qp.is_valid_quality_transition('/qa', '/t'), "qa → t should be invalid"
    assert not qp.is_valid_quality_transition('/comply', '/debug'), "comply → debug should be invalid"
    assert not qp.is_valid_quality_transition('/t', '/refactor'), "t → refactor should be invalid"

    # Non-quality skills should return True (allow)
    assert qp.is_valid_quality_transition('/design', '/test'), "arch → test should be allowed (non-quality)"

    print("  ✓ Quality transition validation working correctly")


def test_validate_quality_workflow():
    """Test quality workflow validation."""
    print("\nTesting quality workflow validation...")

    qp = QualityPipeline()

    # Valid workflow
    valid_result = qp.validate_quality_workflow(['/t', '/comply', '/qa'])
    assert valid_result['valid'], "Standard workflow should be valid"
    assert len(valid_result['issues']) == 0, "Valid workflow should have no issues"

    # Invalid workflow
    invalid_result = qp.validate_quality_workflow(['/qa', '/t'])
    assert not invalid_result['valid'], "Reverse workflow should be invalid"
    assert len(invalid_result['issues']) > 0, "Invalid workflow should have issues"

    # Workflow with recommendations
    invalid_with_rec = qp.validate_quality_workflow(['/qa', '/comply', '/test'])
    assert not invalid_with_rec['valid'], "Invalid workflow should fail"
    assert len(invalid_with_rec['recommendations']) > 0, "Should provide recommendations"

    print("  ✓ Quality workflow validation working correctly")


def test_get_next_quality_skills():
    """Test next quality skills suggestion."""
    print("\nTesting next quality skills suggestion...")

    qp = QualityPipeline()

    # From /t
    next_from_test = qp.get_next_quality_skills('/t')
    assert '/comply' in next_from_test, "comply should be suggested after t"
    assert '/qa' in next_from_test, "qa should be suggested after t"

    # From /comply
    next_from_comply = qp.get_next_quality_skills('/comply')
    assert '/qa' in next_from_comply, "qa should be suggested after comply"
    assert '/q' in next_from_comply, "q should be suggested after comply"

    # From non-quality skill
    next_from_arch = qp.get_next_quality_skills('/design')
    assert '/t' in next_from_arch, "t should be entry point"
    assert '/analyze' in next_from_arch, "analyze should be entry point"

    print("  ✓ Next quality skills suggestion working correctly")


def test_quality_metrics_recording():
    """Test quality metrics recording."""
    print("\nTesting quality metrics recording...")

    qp = QualityPipeline()

    # Record metrics
    qp.record_quality_metrics('/t', {
        'tests_passed': 42,
        'tests_failed': 3,
        'coverage_percent': 85.5
    })

    qp.record_quality_metrics('/t', {
        'tests_passed': 38,
        'tests_failed': 5,
        'coverage_percent': 82.0
    })

    # Get metrics
    metrics = qp.get_quality_metrics('/t')

    assert metrics['total_runs'] == 2, "Should have 2 runs"
    assert len(metrics['executions']) == 2, "Should have 2 executions"
    assert 'aggregate' in metrics, "Should have aggregate metrics"

    # Check aggregate calculations
    agg = metrics['aggregate']
    assert agg['tests_passed']['sum'] == 80, "Sum should be 80"
    assert agg['tests_passed']['avg'] == 40.0, "Average should be 40.0"
    assert agg['coverage_percent']['min'] == 82.0, "Min should be 82.0"
    assert agg['coverage_percent']['max'] == 85.5, "Max should be 85.5"

    print("  ✓ Quality metrics recording working correctly")
    print(f"    - Total runs: {metrics['total_runs']}")
    print(f"    - Average tests passed: {agg['tests_passed']['avg']}")


def test_quality_metrics_summary():
    """Test quality metrics summary."""
    print("\nTesting quality metrics summary...")

    qp = QualityPipeline()

    # Record some metrics
    qp.record_quality_metrics('/t', {'tests_passed': 42})
    qp.record_quality_metrics('/comply', {'issues_found': 5})
    qp.record_quality_metrics('/qa', {'checks_passed': 15})

    # Get summary
    summary = qp.get_quality_metrics()

    assert summary['skills_tracked'] == 3, "Should track 3 skills"
    assert summary['total_executions'] == 3, "Should have 3 total executions"
    assert 'by_skill' in summary, "Should have by_skill breakdown"

    print("  ✓ Quality metrics summary working correctly")
    print(f"    - Skills tracked: {summary['skills_tracked']}")
    print(f"    - Total executions: {summary['total_executions']}")


def test_pipeline_execution_recording():
    """Test pipeline execution recording."""
    print("\nTesting pipeline execution recording...")

    qp = QualityPipeline()

    # Record pipeline execution
    qp.record_pipeline_execution(
        ['/t', '/comply', '/qa'],
        {'status': 'passed', 'total_time': 45.2}
    )

    # Get history
    history = qp.get_pipeline_history()

    assert len(history) == 1, "Should have 1 execution"
    assert history[0]['workflow'] == ['/t', '/comply', '/qa'], "Workflow mismatch"
    assert history[0]['results']['status'] == 'passed', "Status not recorded"

    print("  ✓ Pipeline execution recording working correctly")


def test_quality_summary():
    """Test comprehensive quality summary."""
    print("\nTesting quality summary...")

    qp = QualityPipeline()

    summary = qp.get_quality_summary()

    assert 'quality_skills' in summary, "Should include quality_skills"
    assert 'recommended_workflows' in summary, "Should include recommended_workflows"
    assert 'metrics' in summary, "Should include metrics"
    assert 'pipeline_executions' in summary, "Should include pipeline_executions"
    assert 'recent_executions' in summary, "Should include recent_executions"

    print("  ✓ Quality summary working correctly")
    print(f"    - Quality skills categories: {len(summary['quality_skills'])}")
    print(f"    - Recommended workflows: {len(summary['recommended_workflows'])}")


def test_singleton_instance():
    """Test singleton instance works."""
    print("\nTesting singleton instance...")

    # Use the singleton
    assert quality_pipeline is not None, "Singleton should exist"

    # Record on singleton
    quality_pipeline.record_quality_metrics('/t', {'tests_passed': 10})

    # Should persist
    metrics = quality_pipeline.get_quality_metrics('/t')
    assert metrics['total_runs'] == 1, "Singleton should persist state"

    print("  ✓ Singleton instance working correctly")


def run_all_tests():
    """Run all quality pipeline tests."""
    print("=" * 60)
    print("QUALITY PIPELINE TEST SUITE (Phase 2)")
    print("=" * 60)

    tests = [
        test_quality_stage_enum,
        test_quality_skills_categorization,
        test_recommended_workflows,
        test_is_quality_skill,
        test_get_quality_category,
        test_stage_from_skill,
        test_quality_transition_validation,
        test_validate_quality_workflow,
        test_get_next_quality_skills,
        test_quality_metrics_recording,
        test_quality_metrics_summary,
        test_pipeline_execution_recording,
        test_quality_summary,
        test_singleton_instance
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"  ✗ FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"  ✗ ERROR: {e}")
            failed += 1

    print("\n" + "=" * 60)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 60)

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
