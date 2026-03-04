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
- **No File Headers**: Do not add module-level docstrings that describe what the file replaces, how it changed, or its history. Comments should describe current behaviour, not past states.

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

## 📂 Project Structure
```
src/brad/
├── core/                    # Configuration, database, ORM models, Pydantic schemas
│   ├── config.py            # pydantic-settings (env vars + Docker secrets)
│   ├── db.py                # SQLAlchemy engine + session
│   ├── schemas.py           # Pydantic validation models
│   └── models/              # SQLAlchemy ORM models
├── repositories/            # Data access layer (thin SQLAlchemy wrappers)
├── services/                # Business logic (seeding, backup, ingestion)
├── frontend/                # Streamlit application
└── cli.py                   # Click CLI entry point

data/
├── seed/                    # YAML initial/seed data (loaded by `brad db seed`)
├── backup/                  # Database backups
dbt/                         # DBT project (analytical layer)
```

## 🔧 Tech Stack
- **ORM**: SQLAlchemy 2.x (mapped_column style)
- **Validation**: Pydantic 2.x
- **Config**: pydantic-settings
- **CLI**: Click
- **Frontend**: Streamlit
- **Database**: PostgreSQL
- **Package Manager**: uv
