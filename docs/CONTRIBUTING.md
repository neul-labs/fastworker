# Contributing to FastQueue

Thank you for your interest in contributing to FastQueue! We welcome contributions from the community.

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/yourusername/fastqueue.git`
3. Create a new branch: `git checkout -b feature/your-feature-name`
4. Make your changes
5. Commit your changes: `git commit -am "Add some feature"`
6. Push to the branch: `git push origin feature/your-feature-name`
7. Submit a pull request

## Development Setup

1. Install Poetry: `pip install poetry`
2. Install dependencies: `poetry install`
3. Activate the virtual environment: `poetry shell`

## Code Style

We use Black for code formatting and Flake8 for linting:

```bash
# Format code
poetry run black .

# Lint code
poetry run flake8
```

## Testing

Please ensure all tests pass before submitting a pull request:

```bash
# Run all tests
poetry run pytest

# Run tests with coverage
poetry run pytest --cov=fastqueue
```

## Documentation

If you're adding new features or changing existing functionality, please update the documentation accordingly.

## Pull Request Process

1. Ensure any install or build dependencies are removed before the end of the layer when doing a build
2. Update the README.md with details of changes to the interface, this includes new environment variables, exposed ports, useful file locations and container parameters
3. Increase the version numbers in any examples files and the README.md to the new version that this Pull Request would represent
4. You may merge the Pull Request in once you have the sign-off of two other developers, or if you do not have permission to do that, you may request the second reviewer to merge it for you

## Reporting Issues

Please use the GitHub issue tracker to report bugs or suggest features.

When reporting a bug, please include:

1. Your operating system name and version
2. Any details about your local setup that might be helpful in troubleshooting
3. Detailed steps to reproduce the bug

## Code of Conduct

This project adheres to the Python Software Foundation Code of Conduct. By participating, you are expected to uphold this code.