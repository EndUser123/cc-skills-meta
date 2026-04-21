import unittest
from py.models import ReasoningState, Claim, ClaimStatus, Severity, TaskType, DataClass, ClassificationResult, ExternalResult, Finding, ExternalRole
from py.context_builder import build_context
from py.policies import should_use_external, OrchestratorConfig
from py.synthesizer import reconcile

class TestReasonPPX(unittest.TestCase):
    def test_privacy_leak_pruned(self):
        # VERIFY: privacy keywords NO LONGER block external calls (pruned to alleviate deadlock)
        query = "Review this private code containing api_key='12345'"
        context = build_context(query)
        config = OrchestratorConfig()
        state = ReasoningState(query=query)
        state.context = context
        state.task = ClassificationResult(task_type=TaskType.CODEREVIEW, confidence=1.0)
        
        # should_use_external(state, config) should now return True
        self.assertTrue(should_use_external(state, config), "Privacy check was NOT pruned (deadlock remains)!")

    def test_prescriptive_strategy_shift(self):
        # VERIFY: high-impact challenge triggers a prescriptive strategy shift
        state = ReasoningState(query="test")
        state.claims = [
            Claim(id="C1", text="Critical claim", status=ClaimStatus.VERIFIED, impact=Severity.HIGH)
        ]
        
        res = ExternalResult(
            role=ExternalRole.VERIFY,
            provider="gemini",
            ok=True,
            normalized=[
                Finding(
                    role=ExternalRole.VERIFY,
                    provider="gemini",
                    summary="C1 is wrong",
                    severity=Severity.HIGH
                )
            ]
        )
        state.external_results = [res]
        
        reconcile(state)
        
        self.assertTrue("SHIFT:" in state.strategy_shift, "Strategy shift was not prescriptive!")
        self.assertEqual(state.claims[0].status, ClaimStatus.INFERRED)

    def test_reconciliation_logic_error(self):
        # BUG: any challenge downgrades all high-impact claims
        state = ReasoningState(query="test")
        state.claims = [
            Claim(id="C1", text="The sky is blue", status=ClaimStatus.VERIFIED, impact=Severity.HIGH),
            Claim(id="C2", text="The moon is made of cheese", status=ClaimStatus.VERIFIED, impact=Severity.HIGH)
        ]
        
        # External result only challenges C2
        res = ExternalResult(
            role=ExternalRole.VERIFY,
            provider="gemini",
            ok=True,
            normalized=[
                Finding(
                    role=ExternalRole.VERIFY,
                    provider="gemini",
                    summary="Claim C2 is wrong and moon is rock",
                    severity=Severity.HIGH
                )
            ]
        )
        state.external_results = [res]
        
        reconcile(state)
        
        print(f"DEBUG: C1 status: {state.claims[0].status}")
        print(f"DEBUG: C2 status: {state.claims[1].status}")
        
        # C2 should be downgraded to INFERRED (from VERIFIED), but C1 should NOT be.
        self.assertEqual(state.claims[0].status, ClaimStatus.VERIFIED, "C1 was incorrectly downgraded")
        self.assertEqual(state.claims[1].status, ClaimStatus.INFERRED, "C2 was not downgraded")

if __name__ == "__main__":
    unittest.main()
