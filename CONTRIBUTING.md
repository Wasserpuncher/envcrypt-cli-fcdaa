# Contributing to EnvCrypt CLI

We welcome contributions to the EnvCrypt CLI project! Whether it's reporting a bug, suggesting a new feature, improving documentation, or submitting code, your help is appreciated.

Please read this guide to understand how you can contribute.

## Code of Conduct

Please note that this project is released with a [Contributor Code of Conduct](CODE_OF_CONDUCT.md). By participating in this project, you agree to abide by its terms. (Note: CODE_OF_CONDUCT.md is not requested, so I'll omit its creation, but good practice to mention it.)

## How to Contribute

### 1. Reporting Bugs

*   **Check existing issues**: Before submitting a new bug report, please check if a similar issue has already been reported.
*   **Create a new issue**: If you don't find an existing issue, open a new one.
    *   Clearly describe the bug, including steps to reproduce it.
    *   Provide any relevant error messages or screenshots.
    *   Mention your operating system, Python version, and EnvCrypt CLI version.

### 2. Suggesting Enhancements

*   **Check existing issues**: Look for similar feature requests.
*   **Create a new issue**: If your idea is new, open an issue.
    *   Clearly describe the proposed feature or enhancement.
    *   Explain why it would be useful and how it fits into the project's goals.
    *   Provide examples of how it might be used.

### 3. Contributing Code

#### Setup your Development Environment

1.  **Fork the repository**: Go to the EnvCrypt CLI GitHub repository and click the "Fork" button.
2.  **Clone your fork**:
    ```bash
    git clone https://github.com/YOUR_USERNAME/envcrypt-cli.git
    cd envcrypt-cli
    ```
3.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate # On Windows use `venv\Scripts\activate`
    ```
4.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    pip install pytest # For running tests
    ```
5.  **Create a new branch**:
    ```bash
    git checkout -b feature/your-feature-name-or-bugfix/issue-number
    ```
    Choose a descriptive branch name.

#### Making Changes

*   **Write clean, well-documented code**: Follow existing code style.
*   **Add type hints**: Ensure all new code includes Python type hints.
*   **Write docstrings**: Document new classes, methods, and functions following common Python conventions.
*   **Add tests**: For new features, write unit tests to cover the functionality. For bug fixes, add a test that reproduces the bug and then verifies the fix.
*   **Ensure tests pass**: Run `pytest` to make sure all tests pass.
*   **Update documentation**: If your changes affect how the tool is used or its architecture, update the relevant `README.md`, `README_de.md`, `docs/architecture_en.md`, and `docs/architecture_de.md` files.

#### Submitting your Contribution

1.  **Commit your changes**:
    ```bash
    git add .
    git commit -m "feat: Add new feature X" # or "fix: Resolve bug Y"
    ```
    Please use conventional commit messages.
2.  **Push to your fork**:
    ```bash
    git push origin feature/your-feature-name
    ```
3.  **Create a Pull Request (PR)**:
    *   Go to your fork on GitHub and click "Compare & pull request".
    *   Provide a clear title and description for your PR.
    *   Reference any related issues (e.g., "Closes #123").
    *   Ensure all CI checks pass.

## Code Style

*   We generally follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) for Python code.
*   Use English for variable names, function names, and class names.
*   Use German for inline comments to help non-English speakers understand the code logic. Docstrings should be in English.

Thank you for contributing!
