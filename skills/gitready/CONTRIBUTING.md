# Contributing to gitready

Thank you for your interest in contributing to gitready! This document provides guidelines and instructions for contributing.

## Development Setup

### Prerequisites

- Claude Code CLI
- Python 3.14+ (for running tests)
- Git

### Local Development

1. **Fork and clone the repository**
   ```bash
   git clone https://github.com/yourusername/gitready.git
   cd gitready
   ```

2. **Create a junction for local development**
   ```powershell
   # Windows (no admin required)
   New-Item -ItemType Junction -Path "P:\.claude\skills\gitready" -Target "P:\packages\gitready"
   ```

3. **Make your changes**
   - Edit files in `P:/packages/gitready`
   - Changes are immediately available via the junction

4. **Run tests**
   ```bash
   cd P:/packages/gitready
   pytest tests/ -v
   ```

5. **Check code quality**
   ```bash
   ruff check core/
   ruff format core/
   ```

## Contribution Guidelines

### Code Style

- Follow existing code style and patterns
- Use meaningful variable and function names
- Add docstrings to functions and classes
- Keep functions focused and concise

### Commit Messages

Follow conventional commit format:
```
feat: add new feature
fix: resolve bug
docs: update documentation
test: add tests
refactor: code refactoring
chore: maintenance tasks
```

### Testing

- Write tests for new functionality
- Ensure all tests pass before submitting PR
- Aim for good test coverage

### Documentation

- Update README.md if adding user-facing features
- Update CHANGELOG.md for significant changes
- Add inline documentation for complex logic

## Pull Request Process

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests and ensure they pass
5. Commit your changes (`git commit -m 'feat: add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## Reporting Issues

When reporting issues, please include:
- Clear description of the problem
- Steps to reproduce
- Expected behavior
- Actual behavior
- Environment details (OS, Python version, etc.)

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
