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
- **Focus**: Describe the code *as is* in its final proposed state. Do not provide a changelog or a timeline of delta changes made since the PR was opened. Focus on the final context, key features, and file modifications.

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

## ⚠️ Common Gotchas & Patterns
- **Subprocess Environments**: When using `subprocess.run`, NEVER replace the environment entirely via `env={"VAR": "value"}` as this deletes the system `PATH` and breaks binary discovery. Always merge: `env={**os.environ, "VAR": "value"}`.
- **Lazy Initialization**: Database engines (`get_engine()`) should be cached using `@lru_cache` and ORM models must be imported locally inside commands. This prevents CLI crashes when running simple commands (like `brad --help`) in environments without database credentials.
- **Idempotency**: Data ingestion and seeding scripts must be fully idempotent. Use natural key lookups and upserts rather than blind inserts to ensure scripts can be run repeatedly.
- **Technical Debt**: When discovering non-critical tech debt, duplicated logic, or dead code during PR reviews or refactoring tasks, document them by creating GitHub issues (e.g., via `gh issue create`) rather than attempting major unplanned restructuring.
