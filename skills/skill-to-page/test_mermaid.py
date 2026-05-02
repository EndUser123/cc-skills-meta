import sys
sys.path.insert(0, 'P:/packages/.github_repos/browser-harness')

from admin import ensure_daemon, restart_daemon
from helpers import new_tab, wait_for_load, js, screenshot

restart_daemon()
ensure_daemon()
new_tab('http://localhost:9795')
wait_for_load()

# Check SVG count
svg_count = js("document.querySelectorAll('#diagramStage svg').length")
print(f'svg_count: {svg_count}')

# Check if mermaid loaded
status = js("typeof window.__mermaid")
print(f'window.__mermaid type: {status}')

# Check if mermaid ready
ready = js("window.__mermaidReady ? 'Promise exists' : 'undefined'")
print(f'window.__mermaidReady: {ready}')

# Check page title
title = js("document.title")
print(f'Page title: {title}')