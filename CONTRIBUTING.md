# Contributing to FastWorker

Thank you for your interest in contributing to FastWorker!

## Development Setup

1. **Clone and Install**
   ```bash
   git clone https://github.com/dipankar/fastworker.git
   cd fastworker
   poetry install
   ```

2. **Verify Installation**
   ```bash
   poetry run pytest
   poetry run fastworker --help
   ```

## Development Workflow

### Code Style
- Use `poetry run black .` for formatting
- Use `poetry run flake8` for linting
- Follow existing code patterns and conventions
- Add type hints where appropriate

### Testing
- Write tests for all new features and bug fixes
- Place tests in the `tests/` directory
- Ensure all tests pass: `poetry run pytest`
- Aim for good test coverage of new code

### Commits
- Use clear, descriptive commit messages
- Reference issue numbers when applicable
- Keep commits focused and atomic

## Pull Request Process

1. **Fork** the repository
2. **Create a feature branch** from `main`
3. **Make changes** with tests
4. **Ensure tests pass** and code is formatted
5. **Submit pull request** with clear description

## Reporting Issues

When reporting bugs, please include:
- Python version and environment details
- Steps to reproduce the issue
- Expected vs actual behavior
- Relevant code snippets or error messages

## Areas for Contribution

- **Documentation improvements**
- **Additional test coverage**
- **Performance optimizations**
- **New networking patterns**
- **Integration examples**

## Code of Conduct

- Be respectful and constructive
- Focus on technical merit
- Help others learn and improve
- Maintain a welcoming environment

## Questions?

Feel free to open an issue for questions about:
- Architecture decisions
- Implementation details
- Contribution ideas
- Development environment setup