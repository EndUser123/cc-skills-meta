import os
import json
from py.main import orchestrate
from py.config import OrchestratorConfig

def test_query_normalization_amnesia():
    query1 = "What is the best way to handle async in Python?"
    query2 = "what is the best way to handle async in python?" # Different case
    
    LEDGER_PATH = os.path.join(".claude", "state", "reason_ppx_ledger.json")
    if os.path.exists(LEDGER_PATH):
        os.remove(LEDGER_PATH)
    
    print(f"Running query 1: '{query1}'")
    orchestrate(query1)
    
    print(f"\nRunning query 2: '{query2}'")
    # If the ledger isn't normalized, this will NOT hit the cache.
    # We can check the execution_notes for 'ledger_hit=true'
    state = orchestrate(query2)
    
    if "ledger_hit=true" in state.execution_notes:
        print("\nSUCCESS: Query was normalized. No amnesia.")
    else:
        print("\nFAILURE: Case-sensitive amnesia detected.")
        # exit(1) # Don't exit yet, let's see if we should fix it.

if __name__ == "__main__":
    test_query_normalization_amnesia()
