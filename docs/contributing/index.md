# Contributing Guide

Thank you for your interest in contributing to BCIpyDummies!

## How to Contribute

### Reporting Bugs

1. Check existing [issues](https://github.com/itsvaalentine/BCIpyDummies/issues) first
2. Create a new issue with:
   - Clear description of the bug
   - Steps to reproduce
   - Expected vs actual behavior
   - System info (Windows version, Python version, Emotiv device)

### Suggesting Features

Open an issue with the "enhancement" label describing:
- The problem you're trying to solve
- Your proposed solution
- Any alternatives you've considered

### Code Contributions

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Write tests for new functionality
4. Ensure all tests pass (`pytest tests/`)
5. Submit a pull request

## Development Setup

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/BCIpyDummies.git
cd BCIpyDummies

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest tests/ -v
```

## Code Style

- Follow PEP 8
- Use type hints
- Write docstrings for public methods
- Keep comments in English (or Spanish if matching existing code)

## Testing

- Write tests for new functionality
- Tests should work without Emotiv hardware (use mocks)
- Target the `windows-latest` GitHub Actions runner

## Pull Request Process

1. Update documentation for any new features
2. Add tests covering your changes
3. Ensure CI passes
4. Request review from maintainers

## Questions?

Open a [discussion](https://github.com/itsvaalentine/BCIpyDummies/discussions) for questions not covered here.
