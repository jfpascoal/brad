# AI Agent Instructions

This document provides project-specific guidelines and conventions that AI agents MUST follow when contributing to the **brad** repository.

## 🛠 Commit Guidelines
- **Granularity**: One task/issue per commit.
- **Prefixes**: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`.
- **Message**: Concise, imperative mood (e.g., "Add feature"), max 100 chars.

## 💻 Code Standards
Code must be simple, readable, modular, and efficient.
- **Self-Documenting**: Write code that explains itself through clear naming and logic.
- **Type Hints**: Use type hints by default for all function signatures and variables.
- **Modularity**: Prioritise short, single-purpose functions/methods.
- **Classes**: Use for dependency injection and state persistence. Each class must have a specific, well-defined purpose.
- **Architecture**: Organise code into modules/abstractions with simple, robust interfaces.

## 🐍 Python Docstrings
Keep docstrings short and to the point. Provide only necessary context for quick understanding.
- **Standard**: PEP 257.
- **Format**:
  - One-liners for simple cases: `"""Summary of functionality."""`
  - For complex cases:
    ```python
    """
    Summary description.

    :param name: description
    :return: description
    :raises Error: conditions
    """
    ```

## 🔀 Pull Request Descriptions
- **Format**: Raw Markdown, UK English.
- **Style**: No emojis, use bullet points, avoid redundancy.
- **Focus**: Context/motivation, key changes, and significant file modifications.
