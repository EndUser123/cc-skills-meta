"""Suggest Field Parser — token-optimized with JSON disk cache."""

import json
import re
from pathlib import Path
from typing import Dict, List, Set


class SuggestFieldParser:
    """Parse suggest fields from skill SKILL.md files.

    Token optimization:
    - Caches parsed graph to JSON on disk (avoids re-parsing 192 YAML frontmatters
      on every new Python process / Claude Code session restart)
    - Falls back to dynamic scan only when cache is missing or corrupt
    - Within a single process, the singleton pattern ensures one parse per lifetime
    """

    SKILLS_PATH = Path("P:/.claude/skills")
    CACHE_PATH = Path("P:/.claude/session_data/suggest_graph.json")

    def __init__(self) -> None:
        self.skills_graph: Dict[str, List[str]] = {}
        self.loaded = False

    def load_all_skills(self) -> Dict[str, List[str]]:
        """Load suggest graph — from disk cache if available, otherwise scan and cache."""
        if self.loaded:
            return self.skills_graph

        cache = self._load_cache()
        if cache is not None:
            self.skills_graph = cache
            self.loaded = True
            return self.skills_graph

        self.skills_graph = self._scan_skills()
        self._save_cache(self.skills_graph)
        self.loaded = True
        return self.skills_graph

    def _load_cache(self) -> Dict[str, List[str]] | None:
        if not self.CACHE_PATH.exists():
            return None
        try:
            with open(self.CACHE_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if isinstance(data, dict) and len(data) > 0:
                return data
        except (json.JSONDecodeError, OSError):
            pass
        return None

    def _save_cache(self, graph: Dict[str, List[str]]) -> None:
        try:
            self.CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
            with open(self.CACHE_PATH, 'w', encoding='utf-8') as f:
                json.dump(graph, f)
        except OSError:
            pass

    def _scan_skills(self) -> Dict[str, List[str]]:
        graph: Dict[str, List[str]] = {}
        for skill_dir in self.SKILLS_PATH.iterdir():
            if not skill_dir.is_dir():
                continue
            skill_file = skill_dir / "SKILL.md"
            if not skill_file.exists():
                continue
            skill_name = f"/{skill_dir.name}"
            suggests = self._parse_skill_file(skill_file)
            if suggests:
                graph[skill_name] = suggests
        return graph

    def _parse_skill_file(self, skill_file: Path) -> List[str]:
        """Extract suggest field via regex (YAML-tolerant)."""
        try:
            with open(skill_file, 'r', encoding='utf-8') as f:
                content = f.read()
        except OSError:
            return []
        if not content.startswith('---'):
            return []
        end_marker = content.find(chr(10) + '---', 4)
        if end_marker == -1:
            return []
        frontmatter = content[3:end_marker]
        match = re.search(r'(?mis)^suggest\s*:\s*(.+)$', frontmatter)
        if not match:
            return []
        raw = match.group(1).strip()
        items = re.findall(r'/([a-z][a-z0-9_-]*)', raw, re.IGNORECASE)
        return ['/' + i.lstrip('/') for i in items]

    def get_suggestions(self, skill_name: str) -> List[str]:
        if not self.loaded:
            self.load_all_skills()
        if not skill_name.startswith('/'):
            skill_name = f'/{skill_name}'
        return self.skills_graph.get(skill_name, [])

    def get_skill_metadata(self, skill_name: str) -> Dict:
        if skill_name.startswith('/'):
            skill_name = skill_name[1:]
        skill_file = self.SKILLS_PATH / skill_name / 'SKILL.md'
        if not skill_file.exists():
            return {}
        try:
            with open(skill_file, 'r', encoding='utf-8') as f:
                content = f.read()
        except OSError:
            return {}
        import yaml
        end_marker = content.find(chr(10) + '---', 4)
        if end_marker == -1:
            return {}
        try:
            return yaml.safe_load(content[3:end_marker]) or {}
        except Exception:
            return {}

    def get_all_skills(self) -> Set[str]:
        if not self.loaded:
            self.load_all_skills()
        return set(self.skills_graph.keys())

    def get_graph(self) -> Dict[str, List[str]]:
        if not self.loaded:
            self.load_all_skills()
        return self.skills_graph.copy()

    def rebuild_cache(self) -> Dict[str, List[str]]:
        """Force rescan and cache refresh. Call after skill registration."""
        self.loaded = False
        self.skills_graph = {}
        return self.load_all_skills()


suggest_parser = SuggestFieldParser()
