import os
import json
from py.main import orchestrate
from py.config import OrchestratorConfig

def test_amnesia_state():
    query = "test query for state amnesia"
    LEDGER_PATH = os.path.join(".claude", "state", "reason_ppx_ledger.json")
    if os.path.exists(LEDGER_PATH):
        os.remove(LEDGER_PATH)
    
    print("Running first time...")
    state1 = orchestrate(query)
    
    if not state1.claims:
        print("FAILURE: First run produced no claims?")
        exit(1)
    
    print(f"First run claims count: {len(state1.claims)}")
    
    print("\nRunning second time (should hit ledger)...")
    state2 = orchestrate(query)
    
    print(f"Second run claims count: {len(state2.claims)}")
    
    if len(state2.claims) == len(state1.claims):
        print("\nSUCCESS: State was fully restored from ledger.")
    else:
        print("\nFAILURE: State was LOST on ledger hit (Amnesia Loop).")
        exit(1)

if __name__ == "__main__":
    test_amnesia_state()
