"""
Master Skill Orchestrator CLI

Robust command-line interface for skill orchestration and workflow management.
Supports colored output, JSON export, and comprehensive error handling.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

# Import orchestrator components
from orchestrator import master_orchestrator


# ==================== OUTPUT FORMATTING ====================

class OutputFormatter:
    """Format CLI output with optional colors and JSON."""

    # ANSI color codes
    COLORS = {
        'reset': '\033[0m',
        'bold': '\033[1m',
        'red': '\033[31m',
        'green': '\033[32m',
        'yellow': '\033[33m',
        'blue': '\033[34m',
        'magenta': '\033[35m',
        'cyan': '\033[36m',
        'white': '\033[37m',
        'dim': '\033[2m',
    }

    def __init__(self, json_mode: bool = False, quiet: bool = False, verbose: bool = False):
        self.json_mode = json_mode
        self.quiet = quiet
        self.verbose = verbose
        self.use_colors = self._supports_color()

    def _supports_color(self) -> bool:
        """Check if terminal supports color output."""
        # Check if we're in a terminal
        if not hasattr(sys.stdout, 'isatty'):
            return False
        if not sys.stdout.isatty():
            return False

        # Windows 10+ supports ANSI colors
        return True

    def color(self, text: str, color_name: str) -> str:
        """Apply color to text if colors are enabled."""
        if not self.use_colors or self.json_mode:
            return text
        code = self.COLORS.get(color_name, '')
        return f"{code}{text}{self.COLORS['reset']}"

    def error(self, message: str) -> None:
        """Print error message."""
        if self.json_mode:
            json.dump({"error": message}, sys.stdout)
            print()
        else:
            print(self.color(f"Error: {message}", 'red'), file=sys.stderr)

    def warn(self, message: str) -> None:
        """Print warning message."""
        if self.json_mode:
            json.dump({"warning": message}, sys.stdout)
            print()
        else:
            if not self.quiet:
                print(self.color(f"Warning: {message}", 'yellow'), file=sys.stderr)

    def info(self, message: str) -> None:
        """Print info message."""
        if not self.quiet and not self.json_mode:
            print(self.color(message, 'cyan'))

    def success(self, message: str) -> None:
        """Print success message."""
        if self.json_mode:
            json.dump({"success": message}, sys.stdout)
            print()
        else:
            print(self.color(message, 'green'))

    def output(self, data: dict | list | str) -> None:
        """Output data in appropriate format."""
        if self.json_mode:
            json.dump(data, sys.stdout, indent=2)
            print()
        else:
            if isinstance(data, dict):
                self._print_dict(data)
            elif isinstance(data, list):
                self._print_list(data)
            else:
                print(data)

    def _print_dict(self, data: dict) -> None:
        """Pretty print dictionary."""
        for key, value in data.items():
            if isinstance(value, (list, dict)):
                value = json.dumps(value, indent=2)
            print(f"  {key}: {value}")

    def _print_list(self, data: list) -> None:
        """Pretty print list."""
        for item in data:
            if isinstance(item, dict):
                self._print_dict(item)
            else:
                print(f"  - {item}")

    def print_header(self, title: str) -> None:
        """Print section header."""
        if not self.json_mode and not self.quiet:
            print()
            print(self.color(f"=== {title} ===", 'bold'))

    def print_subheader(self, title: str) -> None:
        """Print subsection header."""
        if not self.json_mode and not self.quiet:
            print(self.color(f"\n{title}:", 'blue'))

    def print_skill(self, skill_name: str, details: str = "") -> None:
        """Print skill name with optional details."""
        if not self.json_mode:
            skill_colored = self.color(skill_name, 'cyan')
            if details:
                print(f"  {skill_colored}: {details}")
            else:
                print(f"  {skill_colored}")

    def print_metadata(self, metadata: dict) -> None:
        """Print skill metadata."""
        if self.json_mode:
            return

        for key, value in metadata.items():
            if key == 'suggest':
                continue  # Handle separately
            if isinstance(value, list):
                value_str = ', '.join(str(v) for v in value)
            elif isinstance(value, dict):
                value_str = json.dumps(value)
            else:
                value_str = str(value)
            print(f"    {key}: {value_str}")

    def print_suggestions(self, suggestions: list) -> None:
        """Print skill suggestions."""
        if not suggestions:
            if not self.quiet:
                print("    (none)")
            return

        for suggestion in suggestions:
            self.print_skill(suggestion)


# ==================== COMMAND HANDLERS ====================

class CLICommandHandler:
    """Handle CLI commands."""

    def __init__(self, formatter: OutputFormatter):
        self.formatter = formatter
        self.orchestrator = master_orchestrator

    def suggest(self, skill: str) -> int:
        """Show suggested next skills for a given skill."""
        self.formatter.print_header(f"Suggestions for {skill}")

        try:
            suggestions = self.orchestrator.get_workflow_suggestions(skill)

            if self.formatter.json_mode:
                self.formatter.output({
                    "skill": skill,
                    "suggestions": suggestions
                })
            else:
                if suggestions:
                    self.formatter.print_subheader("Valid Next Skills")
                    self.formatter.print_suggestions(suggestions)
                else:
                    self.formatter.warn(f"No suggestions found for {skill}")
                    self.formatter.info(f"Skill may not exist or has no suggest field")

            return 0

        except Exception as e:
            self.formatter.error(f"Failed to get suggestions: {e}")
            return 1

    def info(self, skill: str) -> int:
        """Show comprehensive information about a skill."""
        self.formatter.print_header(f"Skill Info: {skill}")

        try:
            info = self.orchestrator.get_skill_info(skill)

            if self.formatter.json_mode:
                self.formatter.output(info)
                return 0

            # Pretty print
            metadata = info.get('metadata', {})
            if not metadata:
                self.formatter.warn(f"Skill '{skill}' not found or has no metadata")
                return 1

            # Basic info
            print(f"  Skill: {self.formatter.color(skill, 'cyan')}")
            print(f"  Type: {self.formatter.color('Python Orchestrator', 'green') if info.get('is_python_orchestrator') else 'CLI Skill'}")
            print(f"  Strategic: {self.formatter.color('Yes', 'green') if info.get('is_strategic') else 'No'}")

            # Metadata
            if metadata:
                self.formatter.print_subheader("Metadata")
                self.formatter.print_metadata(metadata)

            # Suggestions
            suggests = info.get('suggests', [])
            if suggests:
                self.formatter.print_subheader("Suggests")
                self.formatter.print_suggestions(suggests)

            # Suggested by
            suggested_by = info.get('suggested_by', [])
            if suggested_by:
                self.formatter.print_subheader("Suggested By")
                for from_skill in suggested_by:
                    self.formatter.print_skill(from_skill)

            return 0

        except Exception as e:
            self.formatter.error(f"Failed to get skill info: {e}")
            return 1

    def validate(self, workflow: str) -> int:
        """Validate a workflow sequence."""
        try:
            # Parse workflow (comma or space separated)
            workflow_list = [w.strip() for w in workflow.replace(',', ' ').split() if w.strip()]

            if len(workflow_list) < 2:
                self.formatter.error("Workflow must contain at least 2 skills")
                self.formatter.info("Example: orchestrator validate '/nse /design /r'")
                return 1

            self.formatter.print_header(f"Workflow Validation")

            validation = self.orchestrator.validate_workflow(workflow_list)

            if self.formatter.json_mode:
                self.formatter.output(validation)
                return 0 if validation['valid'] else 1

            # Pretty print
            workflow_str = ' → '.join(workflow_list)
            print(f"  Workflow: {self.formatter.color(workflow_str, 'cyan')}")

            if validation['valid']:
                self.formatter.success("✓ Valid workflow")
                return 0
            else:
                self.formatter.error("✗ Invalid workflow")

                if validation['issues']:
                    self.formatter.print_subheader("Issues")
                    for issue in validation['issues']:
                        print(f"  Step {issue['step']}: {issue['from']} → {issue['to']}")
                        print(f"    Reason: {issue['reason']}")

                # Show valid alternatives
                if validation['valid_transitions']:
                    self.formatter.print_subheader("Valid Transitions Found")
                    for from_skill, to_skill in validation['valid_transitions']:
                        print(f"  ✓ {from_skill} → {to_skill}")

                return 1

        except Exception as e:
            self.formatter.error(f"Failed to validate workflow: {e}")
            return 1

    def workflow(self, skill: str, depth: int = 3) -> int:
        """Suggest possible workflows starting from a skill."""
        self.formatter.print_header(f"Workflow Suggestions from {skill}")

        try:
            workflows = self.orchestrator.suggest_workflow(skill, depth)

            if not workflows:
                self.formatter.warn(f"No workflow paths found from {skill}")
                return 1

            if self.formatter.json_mode:
                self.formatter.output({
                    "starting_skill": skill,
                    "max_depth": depth,
                    "workflows": workflows
                })
                return 0

            # Pretty print
            print(f"  Max depth: {depth}")
            print(f"  Paths found: {len(workflows)}")

            self.formatter.print_subheader("Possible Workflows")
            for i, path in enumerate(workflows, 1):
                path_str = ' → '.join(path)
                print(f"  {i}. {self.formatter.color(path_str, 'cyan')}")

            return 0

        except Exception as e:
            self.formatter.error(f"Failed to generate workflows: {e}")
            return 1

    def history(self, limit: int = 10) -> int:
        """Show workflow execution history."""
        self.formatter.print_header("Workflow Execution History")

        try:
            execution_log = self.orchestrator.get_execution_log()

            if not execution_log:
                self.formatter.info("No execution history found")
                return 0

            # Apply limit
            if limit > 0:
                execution_log = execution_log[-limit:]

            if self.formatter.json_mode:
                self.formatter.output(execution_log)
                return 0

            # Pretty print
            print(f"  Showing last {len(execution_log)} entries")
            print(f"  Total executions: {len(self.orchestrator.get_execution_log())}")

            self.formatter.print_subheader("Recent Executions")
            for entry in reversed(execution_log):
                timestamp = entry.get('timestamp', 'Unknown time')
                skill = entry.get('skill', 'Unknown')
                status = entry.get('status', 'unknown')

                status_color = 'green' if status == 'success' else 'red'
                status_symbol = '✓' if status == 'success' else '✗'

                print(f"  {status_symbol} {self.formatter.color(skill, 'cyan')} [{self.formatter.color(status, status_color)}]")
                print(f"    Time: {timestamp}")

                suggestions = entry.get('suggestions', [])
                if suggestions:
                    print(f"    Next: {', '.join(suggestions)}")

                workflow_path = entry.get('workflow_path', [])
                if workflow_path:
                    path_str = ' → '.join(workflow_path)
                    print(f"    Path: {path_str}")

                print()

            return 0

        except Exception as e:
            self.formatter.error(f"Failed to retrieve history: {e}")
            return 1

    def stats(self) -> int:
        """Show workflow statistics."""
        self.formatter.print_header("Workflow Statistics")

        try:
            stats = self.orchestrator.get_workflow_stats()

            if self.formatter.json_mode:
                self.formatter.output(stats)
                return 0

            # Pretty print
            print(f"  Total executions: {self.formatter.color(str(stats['total_executions']), 'cyan')}")
            print(f"  Total strategic decisions: {self.formatter.color(str(stats['total_decisions']), 'cyan')}")

            current_workflow = stats.get('current_workflow', [])
            if current_workflow:
                workflow_str = ' → '.join(current_workflow)
                print(f"  Current workflow: {self.formatter.color(workflow_str, 'green')}")
            else:
                print(f"  Current workflow: {self.formatter.color('(none)', 'dim')}")

            workflow_state = stats.get('workflow_state', {})
            print(f"  Workflow stack depth: {workflow_state.get('stack_depth', 0)}")

            print(f"  Skills with suggest fields: {stats['skills_with_suggest_fields']}")
            print(f"  Valid transitions: {workflow_state.get('total_valid_transitions', 0)}")

            invocation_stats = stats.get('invocation_stats', {})
            print(f"  Total skill invocations: {invocation_stats.get('total_invocations', 0)}")

            return 0

        except Exception as e:
            self.formatter.error(f"Failed to retrieve statistics: {e}")
            return 1

    def graph(self, category: Optional[str] = None) -> int:
        """Show skill relationship graph."""
        self.formatter.print_header("Skill Relationship Graph")

        try:
            all_suggestions = self.orchestrator.get_all_suggestions()

            if not all_suggestions:
                self.formatter.info("No skill relationships found")
                return 0

            # Filter by category if specified
            if category:
                # Normalize category
                if not category.startswith('/'):
                    category = f'/{category}'

                filtered = {k: v for k, v in all_suggestions.items() if k.startswith(category)}
                if not filtered:
                    self.formatter.warn(f"No skills found matching category '{category}'")
                    return 1
                all_suggestions = filtered

            if self.formatter.json_mode:
                self.formatter.output(all_suggestions)
                return 0

            # Pretty print
            print(f"  Skills with suggest fields: {len(all_suggestions)}")

            self.formatter.print_subheader("Skill Transitions")
            for from_skill in sorted(all_suggestions.keys()):
                to_skills = all_suggestions[from_skill]
                skills_str = ', '.join(to_skills) if to_skills else '(none)'
                print(f"  {self.formatter.color(from_skill, 'cyan')} → {skills_str}")

            # Show summary
            total_transitions = sum(len(v) for v in all_suggestions.values())
            print(f"\n  Total transitions: {total_transitions}")

            return 0

        except Exception as e:
            self.formatter.error(f"Failed to retrieve graph: {e}")
            return 1

    def invoke(self, skill: str, args: list) -> int:
        """Invoke a skill through the orchestrator."""
        self.formatter.print_header(f"Invoking {skill}")

        try:
            # Parse args if provided
            args_dict = {}
            if args:
                for arg in args:
                    if '=' in arg:
                        key, value = arg.split('=', 1)
                        args_dict[key] = value
                    else:
                        # Positional arg
                        args_dict.setdefault('_', []).append(arg)

            result = self.orchestrator.invoke_skill(skill, args_dict)

            if self.formatter.json_mode:
                self.formatter.output(result)
                return 0 if result.get('status') != 'failed' else 1

            # Pretty print
            status = result.get('status', 'unknown')
            if status == 'success' or status == 'requires_claude_code_context':
                self.formatter.success(f"✓ Skill invoked successfully")

                # Show result details
                if 'result' in result:
                    print(f"  Result: {result['result']}")

                # Show suggestions
                suggestions = result.get('suggested_next_skills', [])
                if suggestions:
                    self.formatter.print_subheader("Suggested Next")
                    self.formatter.print_suggestions(suggestions)

                # Show warnings
                if 'message' in result:
                    self.formatter.info(result['message'])

                return 0

            else:
                self.formatter.error(f"✗ Skill invocation failed")

                if 'error' in result:
                    print(f"  Error: {result['error']}")

                if 'valid_next_skills' in result:
                    self.formatter.print_subheader("Valid Next Skills")
                    self.formatter.print_suggestions(result['valid_next_skills'])

                return 1

        except Exception as e:
            self.formatter.error(f"Failed to invoke skill: {e}")
            return 1


# ==================== MAIN CLI ====================

def build_parser() -> argparse.ArgumentParser:
    """Build argument parser with all commands."""
    parser = argparse.ArgumentParser(
        prog='orchestrator',
        description='Master Skill Orchestrator - Route and manage Claude Code skills',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  orchestrator suggest /nse              Show suggestions for /nse skill
  orchestrator info /design                Show detailed info about /design
  orchestrator validate "/nse,/design"     Validate workflow sequence
  orchestrator workflow /nse --depth 2   Suggest workflows from /nse
  orchestrator history --limit 5         Show last 5 executions
  orchestrator stats                     Show workflow statistics
  orchestrator graph                     Show all skill relationships
  orchestrator invoke /nse               Invoke a skill

For more information, use: orchestrator <command> --help
        """
    )

    # Global options
    parser.add_argument(
        '--json',
        action='store_true',
        help='Output in JSON format (useful for scripting)'
    )
    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Suppress info messages (errors still shown)'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )
    parser.add_argument(
        '--version',
        action='version',
        version='%(prog)s 1.0.0'
    )

    # Subcommands
    subparsers = parser.add_subparsers(
        dest='command',
        title='commands',
        description='Available commands for skill orchestration',
        metavar='<command>',
        help='Command to execute'
    )

    # suggest command
    suggest_parser = subparsers.add_parser(
        'suggest',
        help='Show suggested next skills for a given skill',
        description='Show which skills are suggested after a given skill completes',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  orchestrator suggest /nse
  orchestrator suggest /design
        """
    )
    suggest_parser.add_argument(
        'skill',
        help='Skill name (with or without leading /)'
    )

    # info command
    info_parser = subparsers.add_parser(
        'info',
        help='Show comprehensive information about a skill',
        description='Display detailed metadata, suggestions, and relationships for a skill',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  orchestrator info /nse
  orchestrator info /design
        """
    )
    info_parser.add_argument(
        'skill',
        help='Skill name (with or without leading /)'
    )

    # validate command
    validate_parser = subparsers.add_parser(
        'validate',
        help='Validate a workflow sequence',
        description='Check if a sequence of skills is valid based on suggest fields',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  orchestrator validate "/nse,/design,/r"
  orchestrator validate "/nse /design /r"
        """
    )
    validate_parser.add_argument(
        'workflow',
        help='Workflow sequence (comma or space separated skill names)'
    )

    # workflow command
    workflow_parser = subparsers.add_parser(
        'workflow',
        help='Suggest possible workflows from a skill',
        description='Generate possible workflow paths starting from a given skill',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  orchestrator workflow /nse
  orchestrator workflow /design --depth 2
        """
    )
    workflow_parser.add_argument(
        'skill',
        help='Starting skill name'
    )
    workflow_parser.add_argument(
        '--depth', '-d',
        type=int,
        default=3,
        help='Maximum depth to explore (default: 3)'
    )

    # history command
    history_parser = subparsers.add_parser(
        'history',
        help='Show workflow execution history',
        description='Display recent skill invocations and their context',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  orchestrator history
  orchestrator history --limit 20
        """
    )
    history_parser.add_argument(
        '--limit', '-l',
        type=int,
        default=10,
        help='Number of entries to show (default: 10, use -1 for all)'
    )

    # stats command
    stats_parser = subparsers.add_parser(
        'stats',
        help='Show workflow statistics',
        description='Display statistics about skill invocations and workflows',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    # graph command
    graph_parser = subparsers.add_parser(
        'graph',
        help='Show skill relationship graph',
        description='Display all skill transitions based on suggest fields',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  orchestrator graph
  orchestrator graph --filter /nse
        """
    )
    graph_parser.add_argument(
        '--filter', '-f',
        dest='category',
        help='Filter by skill category (e.g., /nse, /design)'
    )

    # invoke command
    invoke_parser = subparsers.add_parser(
        'invoke',
        help='Invoke a skill through the orchestrator',
        description='Execute a skill with optional arguments',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  orchestrator invoke /nse
  orchestrator invoke /design key=value
        """
    )
    invoke_parser.add_argument(
        'skill',
        help='Skill name to invoke'
    )
    invoke_parser.add_argument(
        'args',
        nargs='*',
        help='Optional arguments for the skill (key=value format)'
    )

    return parser


def run_cli(args: Optional[list] = None) -> int:
    """
    Main CLI entry point.

    Args:
        args: Command line arguments (uses sys.argv if None)

    Returns:
        Exit code (0 = success, non-zero = error)
    """
    parser = build_parser()

    # Parse arguments
    parsed_args = parser.parse_args(args)

    # Create formatter
    formatter = OutputFormatter(
        json_mode=parsed_args.json,
        quiet=parsed_args.quiet,
        verbose=parsed_args.verbose
    )

    # Show help if no command
    if not parsed_args.command:
        parser.print_help()
        return 0

    # Create command handler
    handler = CLICommandHandler(formatter)

    # Route to appropriate command
    try:
        if parsed_args.command == 'suggest':
            return handler.suggest(parsed_args.skill)

        elif parsed_args.command == 'info':
            return handler.info(parsed_args.skill)

        elif parsed_args.command == 'validate':
            return handler.validate(parsed_args.workflow)

        elif parsed_args.command == 'workflow':
            return handler.workflow(parsed_args.skill, parsed_args.depth)

        elif parsed_args.command == 'history':
            return handler.history(parsed_args.limit)

        elif parsed_args.command == 'stats':
            return handler.stats()

        elif parsed_args.command == 'graph':
            return handler.graph(parsed_args.category)

        elif parsed_args.command == 'invoke':
            return handler.invoke(parsed_args.skill, parsed_args.args)

        else:
            formatter.error(f"Unknown command: {parsed_args.command}")
            return 1

    except KeyboardInterrupt:
        formatter.info("\nOperation cancelled by user")
        return 130  # Standard exit code for Ctrl+C

    except Exception as e:
        formatter.error(f"Unexpected error: {e}")
        if parsed_args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(run_cli())
