# yt-fts Technical Debt & Smell Patterns

Reference this list during the **AUDIT** phase of the Evolve workflow.

## 1. Structural Smells

| Smell                | Indicator                                           | Modern Path                                               |
| -------------------- | --------------------------------------------------- | --------------------------------------------------------- |
| **Circular Imports** | Import errors or `import sys; sys.path...` hack     | Extract shared logic to a `common/` or `utils/` module.   |
| **Large Downloader** | `batch_downloader.py` or similar with CC > 20       | Split into `Worker`, `RateLimiter`, and `RetryStrategy`.  |
| **Global Path Hack** | `sys.path.insert(0, ...)`                           | Move to proper `pyproject.toml` or `src/` prefix imports. |
| **Anemic Models**    | Classes that are just dictionaries without behavior | Convert to Pydantic V2 models with validation logic.      |
| **Orphaned Logic**   | Functions with zero imports/calls after refactor    | Purge in Phase 3.                                         |

## 2. Python 2025 Antipatterns

- **Legacy Config**: Using `os.getenv` or `configparser`.
  - _Refactor to:_ `pydantic-settings`.
- **Blocking Async**: Using `requests` or `time.sleep` inside `async def`.
  - _Refactor to:_ `httpx` and `asyncio.sleep`.
- **Manual Tasks**: Using `asyncio.create_task` without tracking or exception handling.
  - _Refactor to:_ `asyncio.TaskGroup`.
- **API Drift**: Using deprecated methods (e.g., Pydantic V1 style).
  - _Refactor to:_ latest 2025 API patterns.

## 3. Project-Specific Debt

- **SQLite Locking**: Long-running transactions blocking status queries.
  - _Fix:_ Use RO mode for readers and active retries for writers.
- **Rich Spacing**: Direct `print()` breaking `rich.Live` displays.
  - _Fix:_ Route all output through the Rich `console` or log queue.

## 4. Complexity Thresholds

- **Function > 50 lines**: High friction for testing.
- **Class > 300 lines**: Cognitive overload for solo dev.
- **CC > 10**: Refactor ASAP.
