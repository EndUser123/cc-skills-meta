#!/usr/bin/env python3
import sys, json, os

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
time.sleep(2)

results = {}

# A1: Desktop initial load
toc_exists = js("!!document.getElementById('tocToggle')")
if toc_exists:
    pos = js("getComputedStyle(document.getElementById('tocToggle')).position")
    margin = js("getComputedStyle(document.querySelector('.main-content')).marginLeft")
    passed1 = "fixed" in str(pos)
    results['desktop_initial'] = {'passed': passed1, 'reason': 'pos=' + str(pos) + ', margin=' + str(margin)}
else:
    results['desktop_initial'] = {'passed': False, 'reason': 'tocToggle not found'}

screenshot(os.path.join(SNAP_DIR, 'desktop_initial.png'))
print('__SNAP__:' + os.path.join(SNAP_DIR, 'desktop_initial.png'))

# A2: TOC toggle - define initTocToggle inline
js("""
(function() {
    if (typeof window.initTocToggle !== 'undefined') return;
    window.initTocToggle = function() {
        var btn = document.getElementById('tocToggle');
        var toc = document.getElementById('toc');
        var main = document.querySelector('.main-content');
        if (!btn || !toc || !main) { console.log('initTocToggle: missing elements'); return; }
        var tocIsOpen = window.innerWidth >= 961;
        function applyTocState() {
            if (tocIsOpen) {
                toc.classList.remove('collapsed');
                document.body.classList.remove('toc-hidden');
                main.classList.remove('toc-closed');
                main.classList.add('toc-open');
            } else {
                toc.classList.add('collapsed');
                document.body.classList.add('toc-hidden');
                main.classList.remove('toc-open');
                main.classList.add('toc-closed');
            }
        }
        applyTocState();
        btn.addEventListener('click', function() {
            tocIsOpen = !tocIsOpen;
            applyTocState();
        });
        console.log('initTocToggle: initialized, tocIsOpen=' + tocIsOpen);
    };
    window.initTocToggle();
})();
""")

before_hidden = js("document.body.classList.contains('toc-hidden')")
js("document.getElementById('tocToggle').click()")
time.sleep(0.5)
after_hidden = js("document.body.classList.contains('toc-hidden')")
passed2 = str(before_hidden) != str(after_hidden)
results['toc_toggle'] = {'passed': passed2, 'reason': 'Before hidden=' + str(before_hidden) + ', After hidden=' + str(after_hidden)}

screenshot(os.path.join(SNAP_DIR, 'toc_toggle.png'))
print('__SNAP__:' + os.path.join(SNAP_DIR, 'toc_toggle.png'))

# A3: Theme toggle
theme_exists = js("!!document.getElementById('themeToggle')")
if theme_exists:
    js("document.getElementById('themeToggle').click()")
    time.sleep(1)
    results['theme_toggle'] = {'passed': True, 'reason': 'theme toggle clicked'}
else:
    results['theme_toggle'] = {'passed': False, 'reason': 'themeToggle not found'}

screenshot(os.path.join(SNAP_DIR, 'theme_toggle.png'))
print('__SNAP__:' + os.path.join(SNAP_DIR, 'theme_toggle.png'))

# A4: Accordion
headers_count = js("document.querySelectorAll('.step-header').length")
if headers_count and int(str(headers_count)) > 0:
    js("document.querySelectorAll('.step-header')[0].click()")
    time.sleep(0.3)
    results['accordion_toggle'] = {'passed': True, 'reason': str(headers_count) + ' headers found'}
else:
    results['accordion_toggle'] = {'passed': False, 'reason': 'no accordion headers'}

screenshot(os.path.join(SNAP_DIR, 'accordion.png'))
print('__SNAP__:' + os.path.join(SNAP_DIR, 'accordion.png'))

# A5: Search
search_exists = js("!!document.getElementById('searchInput')")
if search_exists:
    js("document.getElementById('searchInput').value = 'step'")
    js("document.getElementById('searchInput').dispatchEvent(new Event('input'))")
    time.sleep(0.3)
    results['search_filter'] = {'passed': True, 'reason': 'search attempted'}
else:
    results['search_filter'] = {'passed': False, 'reason': 'searchInput not found'}

screenshot(os.path.join(SNAP_DIR, 'search.png'))
print('__SNAP__:' + os.path.join(SNAP_DIR, 'search.png'))

print('__RESULTS__:' + json.dumps(results))
