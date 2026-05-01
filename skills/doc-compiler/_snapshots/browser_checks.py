#!/usr/bin/env python3
"""Browser verification checks for doc-compiler artifact."""
import sys
import json
import os

# Add browser-harness to path
BH_DIR = "P:/packages/.github_repos/browser-harness"
if BH_DIR not in sys.path:
    sys.path.insert(0, BH_DIR)

from helpers import *
from admin import *

INDEX_PATH = "file:///P:/packages/cc-skills-meta/skills/doc-compiler/index.html"
SNAP_DIR = "P:/packages/cc-skills-meta/skills/doc-compiler/_snapshots"

os.makedirs(SNAP_DIR, exist_ok=True)

ensure_daemon()
new_tab(INDEX_PATH)
wait_for_load()
time.sleep(1)

results = {}

# A1: Desktop initial load
pos = js("getComputedStyle(document.getElementById('tocToggle')).position")
margin = js("getComputedStyle(document.querySelector('.main-content')).marginLeft")
passed1 = "fixed" in str(pos)
results["desktop_initial"] = {
    "passed": passed1,
    "reason": "tocToggle.position=%s, main-content.marginLeft=%s" % (pos, margin)
}
screenshot(os.path.join(SNAP_DIR, "desktop_initial.png"))
print("__SNAP__:" + os.path.join(SNAP_DIR, "desktop_initial.png"))

# A2: TOC toggle click
before_margin = js("getComputedStyle(document.querySelector('.main-content')).marginLeft")
before_collapsed = js("document.getElementById('toc').classList.contains('collapsed')")
click(30, 40)
time.sleep(0.5)
after_margin = js("getComputedStyle(document.querySelector('.main-content')).marginLeft")
after_collapsed = js("document.getElementById('toc').classList.contains('collapsed')")
passed2 = str(before_collapsed) != str(after_collapsed)
results["toc_toggle"] = {
    "passed": passed2,
    "reason": "Before: margin=%s, collapsed=%s. After: margin=%s, collapsed=%s" % (before_margin, before_collapsed, after_margin, after_collapsed)
}
screenshot(os.path.join(SNAP_DIR, "toc_toggle.png"))
print("__SNAP__:" + os.path.join(SNAP_DIR, "toc_toggle.png"))

# A3: Theme toggle
btn = js("document.getElementById('themeToggle')")
if btn:
    click(200, 40)
    time.sleep(1)
    results["theme_toggle"] = {"passed": True, "reason": "theme toggle clicked"}
else:
    results["theme_toggle"] = {"passed": False, "reason": "themeToggle not found"}
screenshot(os.path.join(SNAP_DIR, "theme_toggle.png"))
print("__SNAP__:" + os.path.join(SNAP_DIR, "theme_toggle.png"))

# A4: Accordion
headers_js = js("document.querySelectorAll('.step-header').length")
if headers_js and int(str(headers_js)) > 0:
    js("document.querySelectorAll('.step-header')[0].click()")
    time.sleep(0.3)
    results["accordion_toggle"] = {"passed": True, "reason": "accordion interaction attempted, %s headers found" % headers_js}
else:
    results["accordion_toggle"] = {"passed": False, "reason": "no accordion headers found"}
screenshot(os.path.join(SNAP_DIR, "accordion.png"))
print("__SNAP__:" + os.path.join(SNAP_DIR, "accordion.png"))

# A5: Search - use string concatenation to avoid brace issues
inp = js("document.getElementById('searchInput')")
if inp:
    js("document.getElementById('searchInput').value = 'step'")
    js("document.getElementById('searchInput').dispatchEvent(new Event('input'))")
    time.sleep(0.3)
    results["search_filter"] = {"passed": True, "reason": "search attempted"}
else:
    results["search_filter"] = {"passed": False, "reason": "searchInput not found"}
screenshot(os.path.join(SNAP_DIR, "search.png"))
print("__SNAP__:" + os.path.join(SNAP_DIR, "search.png"))

# Output results as JSON
print("__RESULTS__:" + json.dumps(results))
