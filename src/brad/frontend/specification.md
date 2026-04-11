### Brad Frontend Specification
This document outlines the technical specification and requirements for the frontend of the Brad application.

#### 1. Context
Brad serves as a financial management tool, providing capabilities to track balances across the user's accounts
and financial products. It further enables the analysis of spending/saving patterns and offers insights into financial
health.

#### 2. Objectives
The Brad frontend is the interface between the user and the backend services. It integrates seamlessly with the data
layer (`brad.sql`) to allow the manual input of financial data through the use of forms and interactive components.

#### 3. Design guidelines
- The frontend should make use of the existing data services API (`brad.repositories` and `brad.core.db`). No direct database access should be 
implemented in the frontend module. If extra functionality is needed (missing common access patterns), it should be 
added to the repository layer.
- The frontend should be initialized through the main application entry point (`brad/main.py`) and should adhere to the 
overall application architecture (no direct subprocess calls if avoidable).
- The frontend should be built in Python using streamlit, under `brad.frontend`.
- The python code should be modular, readable and maintainable, following best pythonic coding practices.
- The code should be self-documented where possible, with clear variable, function, class and module names. Docstring should always be included, following style used in the rest of the project. Comments should be used sparingly to explain non-obvious implementation details.
- Tests should be included for all non-trivial functionality and integrations with main module and data service API.
- The user interface should be intuitive and user-friendly, ensuring ease of navigation and data entry.
- The frontend should be minimalistic in design, focusing on functionality and clarity, avoiding unnecessary visual 
elements.

#### 4. Functional requirements

##### 4.1 Data entry
- **Adding account balances**: The user must be able to input one or more balances to an existing account through
a form containing all the elements defined in the data model.
- **Adding financial product valuations**: The user must be able to input one or more valuations to an existing financial 
product through a form containing all the elements defined in the data model.
- **Batch entry**: The user must be able to add multiple balance or valuation entries for the same account or financial 
product in a single session before submitting. Each entry in the batch should display its own date, value, and delta 
from the previous entry (whether from existing data or earlier in the batch).
- **Date input**: The user must be able to specify the date for each balance or valuation entry. The date input should
default to the current date but allow for manual selection of past dates.
- **Last entry preview**: When adding a balance or valuation, the interface must display the most recent entry for the 
selected account or financial product, including the date and value. This helps users verify they are not duplicating 
data and provides context for the new entry.
- **Balance/valuation delta indicator**: When entering a new balance or valuation, the interface must calculate and 
display the difference (delta) from the previous entry once the new value is provided. This should include both the 
absolute change and, where meaningful, the percentage change.

##### 4.2 Entity management
- **Adding new accounts and financial products**: The user must be given the option to add new accounts and financial 
products, as well as all secondary dimensions defined in the data model (provider, holder), except those statically defined
(account type, financial product type).
- **Dynamic selection of existing entities**: When adding balances or valuations, the user should be presented with
dropdown menus or similar UI elements to select from existing accounts, financial products, providers, and holders.
- **Quick entity creation**: From the balance or valuation entry pages, the user must have access to a shortcut 
(button or link) to create a new account or financial product without returning to the main menu.
- **Separate entity management pages**: Creation of new entities (accounts, financial products, providers, holders) 
should be handled on dedicated pages, separate from the data entry forms, to maintain clarity and focus.

##### 4.3 Form handling
- **Form submission and validation**: The user must be provided with a button to submit the input data. The module should
validate the input data before updating the database. If any errors are found, the submission should be rejected with 
an informative error message. If successful, a confirmation message should be displayed.
- **Data persistence**: Upon successful validation, the input data must be persisted to the database under a single SQLAlchemy transaction to guarantee atomic batch inserts.
- **Error handling**: The frontend should gracefully handle any errors that occur during data submission or processing, providing clear feedback to the user.

##### 4.4 Application control
- **Graceful exit**: The user must be able to stop the application through a clearly marked button in the sidebar.
A confirmation dialog must be displayed before terminating the server to prevent accidental exits.

#### 5. Data layer requirements
The data repositories layer (`brad.repositories`) and core models provide the frontend with the following capabilities:
- **Fetch latest balance**: Retrieve the most recent balance entry for a given account.
- **Fetch latest valuation**: Retrieve the most recent valuation entry for a given financial product.
- **List entities**: Provide methods to list all accounts, financial products, providers, and holders.
- **Insert operations**: Insert batch array of balance and valuation entries using SQLAlchemy sessions.
- **Insert entity**: Insert new accounts, financial products, providers, or holders.

#### 6. Implementation details

##### 6.1 Module structure
The frontend is implemented under `brad.frontend` with the following structure:
- `app.py`: Main Streamlit application entry point with navigation, session state initialisation, and exit confirmation dialog.
- `utils.py`: Utility functions for formatting, validation, delta calculation, and data transformation.
- `pages/`: Directory containing page modules:
  - `balance_entry.py`: Balance entry page with batch support and delta preview.
  - `valuation_entry.py`: Valuation entry page with batch support and delta preview.
  - `entity_management.py`: Entity management page with tabs for providers, holders, accounts, and products.

##### 6.2 Data layer extensions
The `brad.repositories` module provides the frontend API with access to:
- Entity listing: Accounts, Financial Products, Providers, Holders, Types mapping via respective repositories.
- Latest entry retrieval: Latest balances and valuations.
- Insert operations: Native SQLAlchemy model commits executed within the Streamlit session factory scope.

##### 6.3 Frontend utilities
The `brad.frontend.utils` module provides helper functions:
- Formatting: `format_currency()`, `format_delta()`
- Data transformation: `get_entity_names()`, `create_entity_map()`
- Validation: `validate_required_fields()`
- Calculation: `calculate_delta()`

##### 6.4 Session state
Streamlit session state is used to maintain:
- `session_factory`: SQLAlchemy `sessionmaker` injected from `brad.core.db.get_session_factory()`.
- `balance_batch`: List of pending balance entries before submission.
- `valuation_batch`: List of pending valuation entries before submission.

##### 6.5 Running the frontend
The frontend is launched via the main CLI:
```bash
brad frontend [--port PORT]
```
This spawns a Streamlit server running the frontend application.




