# Brad Architecture Guide

This document provides a comprehensive overview of the design, structure, and foundational patterns of the `brad` application. It is intended to help developers understand the rationale behind architectural decisions and to guide future development.

## 1. High-Level Architecture Overview

The application follows a **Modular Monolith** approach, heavily inspired by **Domain-Driven Design (DDD)** and **Layered Architecture**. The fundamental goal is the strict separation of concerns: ensuring that database operations, validation rules, business logic, and presentation interactions do not overlap. This guarantees that changes to one layer (such as swapping the frontend framework) have zero impact on the core data integrity.

The codebase is organized into distinct layers:
1. **Core (`src/brad/core/`)**: The foundational configurations, database engine lifecycles, and data definitions (both for relational persistence and runtime data validation).
2. **Repositories (`src/brad/repositories/`)**: The Data Access Layer. This layer physically wraps all direct database communication.
3. **Services (`src/brad/services/`)**: The Business Logic Layer. Complex orchestrations (such as file parsing, bulk seeding) reside here, utilizing multiple repositories to achieve tasks.
4. **Presentation (`src/brad/cli.py` & upcoming Frontend)**: The User Interfaces. They accept commands, create database transaction scopes (Sessions), and pass control to the Services or Repositories without ever writing raw SQL or domain rules.

---

## 2. Core Technologies Explained

The architecture relies on two critical paradigms: persisting data relationally and validating data robustly. We use **SQLAlchemy** and **Pydantic** to solve these explicitly.

### SQLAlchemy (Database ORM)
*Files: `core/models/base.py`, `core/models/reference.py`, `core/models/operational.py`, `core/db.py`*

**Role**: Object-Relational Mapping (ORM). SQLAlchemy translates Python classes into PostgreSQL tables, and queried rows back into Python objects.

**Rationale**:
- **Safety & Security**: Prevents SQL injection by natively parameterizing database interactions.
- **Maintainability**: Define the database layout strictly through Python `Mapped` attribute definitions. Schema changes happen in code, not raw `.sql` files.
- **Relational Integrity**: Uses `ForeignKey` bindings to guarantee referential integrity at the database level (e.g., you cannot create a `FinancialProduct` without valid `ProductType` and `Provider` IDs).
- **Relational Traversing**: Simplifies accessing related datasets (e.g., executing `account.provider.name` automatically resolves the underlying SQL `JOIN`).

**Key Concepts**:
- **DeclarativeBase (`Base`)**: A master class that tracks every defined model mapping.
- **Session**: The "workspace" context for database changes. Handled explicitly to control transactions (`commit` / `rollback`).

### Pydantic (Data Validation)
*Files: `core/schemas.py`, `core/config.py`*

**Role**: Runtime strict type-checking and validation logic.

**Rationale**:
- **Guaranteeing Contracts**: Pydantic parses inputs (like incoming JSON, CLI arguments, or form inputs) and strictly enforces types. If an attribute fails validation, clear errors are raised instantly, preventing poisoned data from reaching the database layer.
- **Configuration Parsing (`pydantic-settings`)**: Validates environment variables and secret files heavily at boot time, ensuring that missing database credentials cause an immediate and descriptive boot failure rather than a cryptic runtime crash.

### Architectural Nuance: Models vs. Schemas
We maintain a strict separation between Database Models (SQLAlchemy) and API/IO Schemas (Pydantic).
- **SQLAlchemy `models/`**: Defines the physical SQL table layout (Primary Keys, Foreign Keys, internal sequence generation).
- **Pydantic `schemas.py`**: Defines the shapes of data entering or leaving the system (e.g., `AccountCreate` for accepting user forms, missing system-generated fields like `updated_at`).

**The Bridge (`from_attributes=True`)**: Our Pydantic "Read" schemas (e.g., `AccountRead`) are configured with `ConfigDict(from_attributes=True)`. This powerful feature allows Pydantic to instantly parse a complex SQLAlchemy object into a detached, safe, in-memory Pydantic view model. This eliminates manual mapping and protects presentation layers from tripping over closed database sessions (avoiding SQLAlchemy's `DetachedInstanceError`).

---

## 3. Module Breakdown

### Bootstrapping (`core/config.py` & `core/db.py`)
- **`config.py`**: Centralizes all configuration state. Parses environment properties and computes derived paths dynamically.
- **`db.py`**: Initializes the global PostgreSQL connection pool (`engine`) and provisions the `SessionLocal` factory to dispense transactions.

### Domain Models (`core/models/`)
- **`base.py`**: Provides the foundational base class and standardizes auditing columns across tables via the `TimestampMixin` snippet (`created_at`, `updated_at`).
- **`reference.py`**: Contains strictly defined "Dimension" lookups (e.g., `currencies`, `account_types`, `transaction_types`). These act as foundational master data.
- **`operational.py`**: Contains the deeply normalized transaction shapes (e.g., `accounts`, `financial_products`, `account_balances`).

### The Data Access Layer (`repositories/`)
- **Goal**: Centralizing database `SELECT`, `INSERT`, `UPDATE`, and `DELETE` logic.
- **`BaseRepository`**: A generic wrapper that handles standard ID-lookups and entity persistence. It remains strictly generic to avoid anti-patterns.
- **Domain Repositories (e.g., `AccountRepository`)**: Extend the `BaseRepository` and host specialized queried calculations (e.g., fetching objects by `name` or retrieving aggregated ranges).

### The Business Logic Layer (`services/`)
- **Goal**: Abstracting complex multi-step logical operations away from interfaces.
- **`seeding.py`**: Handles initialization workflows by determining constraint order dependencies and dynamically applying hierarchical `yaml` data to the relational database.
- **`ingestion.py`**: Contains mapping algorithms connecting human-readable source documents ( spreadsheets) against internal primary keys via the Repositories, handling batch upserts of historical telemetry.
- **`backup.py`**: Interacts dynamically with OS-level paths and child-processes (`pg_dump`) masking implementation details.

### The Entrypoint (`cli.py`)
- Provides command-line access via `click`, delegating commands down into the logical services. Interfaces are completely stateless.

---

## 4. Design Principles & Extensibility

### OLTP Normalization
The system is explicitly modeled around an **OLTP (Online Transaction Processing)** relational foundation. The schema is highly normalized (3NF), maintaining distinct tables.
- **Rationale**: To allow potential frontends (like web interfaces) to rapidly read, insert, or manipulate single logical boundaries securely (such as modifying an Account name without updating thousands of duplicate strings).
- **Integration with OLAP Strategy**: Advanced reporting tools (like Data Build Tool / DBT) treat this system as the master dataset, pulling data outward into distinct, read-optimized "Data Marts" for fast multi-dimensional analytical queries.

### Presentation Context Exclusivity
Database `Session` contexts must remain strictly encapsulated to the lifecycle of the boundary request (e.g., a CLI sub-command run, or an individual web-request). Objects traversing back to the presentation layer MUST be eagerly-loaded for relations or serialized into flat Pydantic models to prevent unexpected lazy-loading network faults.
