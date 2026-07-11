# Contributing to laziest-import

First off, thank you for considering contributing to laziest-import! 🎉

We welcome contributions from everyone, whether you're a first-time contributor or a seasoned developer. This guide will help you understand how to contribute to our project.

## Code of Conduct

Please read our [Code of Conduct](CODE_OF_CONDUCT.md) to understand what kind of behavior we expect from all contributors.

## How Can I Contribute?

There are many ways you can contribute to laziest-import:

### 🐛 Reporting Bugs

Before submitting a bug report, please:
1. Check the [Issues](https://github.com/ChidcGithub/Laziest-import/issues) page to see if it's already reported
2. Check the [Troubleshooting](README.md#troubleshooting) section in the README

When submitting a bug report, please include:
- A clear, descriptive title
- Steps to reproduce the issue
- Expected behavior
- Actual behavior
- Python version
- laziest-import version
- Operating system
- Any relevant error messages

### 💡 Suggesting Enhancements

We love new ideas! When suggesting an enhancement:
1. Use the "enhancement" label in your issue
2. Describe your use case
3. Explain why this enhancement would be useful
4. Provide an example of how it would work

### 📝 Improving Documentation

Great documentation is key! Ways to help:
- Fix typos or clarify existing documentation
- Add examples to show how features work
- Translate documentation to other languages
- Improve the README
- Write tutorials

### 🔧 Code Contributions

#### Getting Started

1. Fork the repository on GitHub
2. Clone your forked repository locally
3. Set up your development environment
4. Create a branch for your work

#### Development Setup

```bash
# Clone the repository
git clone https://github.com/YOUR-USERNAME/Laziest-import.git
cd Laziest-import

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode with all dependencies
pip install -e ".[dev]"
```

#### Branch Naming

Please use descriptive branch names:
- `feature/your-feature-name` for new features
- `fix/your-fix-description` for bug fixes
- `docs/your-documentation-update` for documentation
- `refactor/your-refactor-description` for refactoring

#### Making Changes

1. Create your branch from the `main` branch
2. Make your changes
3. Add tests for any new functionality
4. Ensure all tests pass
5. Commit your changes with clear messages

#### Commit Messages

Use clear and descriptive commit messages:
- `feat: add new feature`
- `fix: resolve bug in X`
- `docs: update documentation`
- `refactor: improve code structure`
- `test: add test for Y`

#### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_basic.py -v

# Run tests with coverage
pytest tests/ --cov=laziest_import

# Run linting
flake8 laziest_import/

# Run type checking
mypy laziest_import/
```

### 🧪 Adding Tests

When adding new features, please include tests:
- Unit tests for individual functions/classes
- Integration tests for interactions between components
- Tests should be in the `tests/` directory
- Follow the existing patterns in the test files

## Pull Request Process

1. Update the README.md with details of changes if applicable
2. Update any documentation affected by your changes
3. The PR title should clearly describe the change
4. The PR description should explain what changed and why
5. Link to any related issues
6. Wait for review from maintainers
7. Address any review comments

## What Makes a Great Contribution?

1. **Follows the existing code style** - Look at the codebase and match the style
2. **Includes tests** - New features should have tests
3. **Has clear documentation** - Code should have comments where needed
4. **Is focused** - One pull request should do one thing only
5. **Descriptive commit messages** - Explains why and what changed

## Development Workflow

1. Start by choosing an issue that interests you
2. Comment on the issue to let people know you're working on it
3. Fork the repository and create a branch
4. Work on your changes locally
5. Push to your fork and submit a pull request
6. Your PR will be reviewed by maintainers

## Need Help?

If you're not sure about something, please ask! You can:
- Open an issue with your question
- Join a discussion on GitHub Discussions
- Reach out to the maintainers

## Recognition

Contributors will be recognized:
- In the contributors section of the README
- In the Git history of the project
- Potentially in release notes

## License

By contributing to laziest-import, you agree that your contributions will be licensed under the MIT license.

---

Thank you for contributing to laziest-import! ❤️
