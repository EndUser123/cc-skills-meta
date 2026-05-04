
import sys, json, os, time
sys.path.insert(0, r"P:/packages/.github_repos/browser-harness")
from helpers import *
from admin import *

INDEX_PATH = "file:///P:/packages/cc-skills-meta/skills/doc-compiler/index.html"
ensure_daemon()
new_tab(INDEX_PATH)
wait_for_load()
time.sleep(2)

toc = js("document.getElementById('tocToggle')")
print("toc:", toc, type(toc))
print("tocToggle found:", bool(toc))

results = {"J1": {"passed": bool(toc), "reason": str(toc)}}
print("__RESULTS__:" + json.dumps(results))
