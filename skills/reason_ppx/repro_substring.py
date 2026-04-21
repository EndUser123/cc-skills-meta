import unittest
from py.models import ReasoningState, Claim, ClaimStatus, Severity, ExternalResult, Finding, ExternalRole
from py.synthesizer import reconcile

class TestSubstringBug(unittest.TestCase):
    def test_claim_id_substring_collision(self):
        # BUG: "C1" is a substring of "C10". Challenging C10 should NOT challenge C1.
        state = ReasoningState(query="test")
        state.claims = [
            Claim(id="C1", text="Claim 1", status=ClaimStatus.VERIFIED, impact=Severity.HIGH),
            Claim(id="C10", text="Claim 10", status=ClaimStatus.VERIFIED, impact=Severity.HIGH)
        ]
        
        # External result ONLY challenges C10
        res = ExternalResult(
            role=ExternalRole.VERIFY,
            provider="gemini",
            ok=True,
            normalized=[
                Finding(
                    role=ExternalRole.VERIFY,
                    provider="gemini",
                    summary="Claim C10 is wrong",
                    severity=Severity.HIGH
                )
            ]
        )
        state.external_results = [res]
        
        reconcile(state)
        
        print(f"DEBUG: C1 status: {state.claims[0].status}")
        print(f"DEBUG: C10 status: {state.claims[1].status}")
        
        self.assertEqual(state.claims[1].status, ClaimStatus.INFERRED, "C10 should be downgraded")
        self.assertEqual(state.claims[0].status, ClaimStatus.VERIFIED, "C1 was incorrectly downgraded due to substring collision!")

if __name__ == "__main__":
    unittest.main()
