import os
import json
import time
from py.main import orchestrate
from py.config import OrchestratorConfig

def test_amnesia_loop():
    query = "test query for amnesia loop"
    
    # 1. Clear ledger
    LEDGER_PATH = os.path.join(".claude", "state", "reason_ppx_ledger.json")
    if os.path.exists(LEDGER_PATH):
        os.remove(LEDGER_PATH)
    
    # 2. Run once to populate
    print("Running first time...")
    orchestrate(query)
    
    # 3. Manually inject "historical evidence" into ledger
    with open(LEDGER_PATH, "r") as f:
        data = json.load(f)
    
    data[query]["final_answer"] = "HISTORICAL_MARKER: This answer came from the ledger."
    
    with open(LEDGER_PATH, "w") as f:
        json.dump(data, f, indent=2)
    
    # 4. Run again and check if it uses the marker
    print("\nRunning second time...")
    state = orchestrate(query)
    
    if "HISTORICAL_MARKER" in state.final_answer:
        print("\nSUCCESS: Historical data was used. Amnesia Loop fixed.")
    else:
        print("\nFAILURE: Historical data was ignored. Amnesia Loop still exists.")
        exit(1)

if __name__ == "__main__":
    test_amnesia_loop()
