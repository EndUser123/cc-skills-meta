from py.models import ReasoningState, ExternalResult, ExternalRole, TaskType, ClassificationResult
from py.synthesizer import finalize_answer

def test_execution_warning():
    state = ReasoningState(query="test")
    state.task = ClassificationResult(task_type=TaskType.GENERAL, confidence=1.0)
    state.internal_draft = "Draft content"
    
    # Mock a failed external call
    failed_res = ExternalResult(
        role=ExternalRole.VERIFY,
        provider="gemini",
        ok=False,
        stderr="AttachConsole failed\nNOT_FOUND: gemini",
        error_type="not_found"
    )
    state.external_results = [failed_res]
    
    answer = finalize_answer(state)
    print("--- FINAL ANSWER ---")
    print(answer)
    
    if "Execution Warnings" in answer and "gemini" in answer and "NOT_FOUND" in answer:
        print("\nSUCCESS: Execution warning surfaced correctly.")
    else:
        print("\nFAILURE: Execution warning MISSING from final answer.")
        exit(1)

if __name__ == "__main__":
    test_execution_warning()
