# Brad - Personal Finance Data Management

Brad is an application built to manage and structure financial data. It is designed with a Modular Monolith architecture inspired by Domain-Driven Design and Layered Architecture. The primary focus is keeping a strict separation of concerns—ensuring that database operations, validation rules, business logic, and presentation interfaces do not overlap.

## Architecture & Structure

The codebase is organized into distinct layers:

1. **Core (`src/brad/core/`)**: Foundational configurations, database engine lifecycles, and data definitions (for both relational persistence and runtime data validation).
2. **Repositories (`src/brad/repositories/`)**: The Data Access Layer. This encapsulates all direct database communication.
3. **Services (`src/brad/services/`)**: The Business Logic Layer. Complex orchestrations, such as spreadsheet parsing, bulk data seeding, and back-ups, reside here and utilize Repositories to perform their tasks.
4. **Presentation (`src/brad/cli.py` & upcoming UI)**: User interfaces accept commands, handle the lifecycle of database transaction scopes (Sessions), and pass control down to Services or Repositories without interacting with raw SQL.

## Core Technologies

- **SQLAlchemy (Database ORM)**: Maps Python classes to PostgreSQL tables. It ensures maintainability by defining the schema strictly through Python code, provides built-in parameterization to avoid SQL injection, and guarantees relational integrity via defined foreign keys.
- **Pydantic (Data Validation)**: Ensures robust runtime type-checking and validation. It prevents poisoned data from reaching the database and parses the environment configuration via `pydantic-settings`. It also acts as a bridge, dynamically translating complex SQLAlchemy instances into safe, detached in-memory view models to protect presentation layers.

## Module Breakdown

- **Bootstrapping**: `core/config.py` centralizes all configuration state and parses environment properties. `core/db.py` initializes the PostgreSQL connection pool and dispenses transaction sessions.
- **Domain Models**: Defined within `core/models/`, split into `reference.py` (dimensional lookup data like currencies and account types) and `operational.py` (deeply normalized schemas for accounts, products, and transactions).
- **Data Access & Logic**: `repositories/` abstract database `SELECT`, `INSERT`, `UPDATE`, and `DELETE` statements. `services/` manage complex multi-step rules like reading Excel files (`ingestion.py`), populating initial tables (`seeding.py`), and managing OS-level backup wrappers (`backup.py`).
- **Entrypoint**: `cli.py` leverages `click` to provide a stateless, command-line interface to the system.

## Database Design

The schema is built around an **OLTP (Online Transaction Processing)** relational foundation. The data is highly normalized (3NF), maintaining distinct tables to ensure data integrity during single logical updates (like modifying an Account's static details).

Advanced reporting, aggregations, and multi-dimensional analytical queries are intended to be processed externally (for example, via Data Build Tool / dbt) by pulling out of this main normalized dataset as the master source of truth.