from py.main import orchestrate
import os

query = "What is the best way to handle asynchronous tasks in Python?"

print("--- FIRST CALL ---")
orchestrate(query)

print("\n--- SECOND CALL ---")
orchestrate(query)

if os.path.exists(".claude/state/reason_ppx_ledger.json"):
    print("\n--- LEDGER CONTENT ---")
    with open(".claude/state/reason_ppx_ledger.json", "r") as f:
        print(f.read())
else:
    print("\n--- NO LEDGER FOUND ---")
