# Project Management System

A comprehensive project management system built with Flask, allowing teams to manage projects, tasks, time tracking, and team collaboration efficiently.

## Features

- Multi-user project management
- Task assignment and tracking
- Time logging and reporting
- Risk assessment
- Department and team management
- Admin dashboard for system management

## Installation

1. Clone the repository
2. Create a virtual environment:
   ```
   python -m venv venv
   venv\Scripts\activate  # Windows
   source venv/bin/activate  # Linux/Mac
   ```
3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Initialize the database:
   ```
   flask db upgrade
   python db_fix.py  # Apply database fixes if needed
   ```
5. Run the application:
   ```
   flask run
   ```

## Database Maintenance

This project includes several utilities for database management:

- `db_fix.py`: Fixes common database issues and relationship problems
- `verify_db.py`: Verifies database integrity
- `scan_arabic_operators.py`: Scans codebase for Arabic logical operators (و, أو)

### Common Database Issues

If you encounter database-related errors:

1. Run database verification:
   ```
   python verify_db.py
   ```

2. Apply database fixes:
   ```
   python db_fix.py
   ```

3. If issues persist, you may need to:
   - Delete the database file (`instance/site.db`)
   - Run migrations:
     ```
     flask db upgrade
     ```
   - Re-run the database fix script:
     ```
     python db_fix.py
     ```

## Database Migrations

### Regular Migration Commands

For normal database updates:

```bash
# Create a new migration
flask db migrate -m "Description of changes"

# Apply pending migrations
flask db upgrade
```

### Troubleshooting Migration Issues

If you encounter migration errors:

1. **Multiple head revisions error**:
   ```bash
   python fix_migrations.py
   flask db upgrade
   ```

2. **Database not up to date error**:
   ```bash
   flask db upgrade
   ```

3. **Reset admin password**:
   ```bash
   python reset_admin.py
   ```

See the [Migration Troubleshooting Guide](docs/MIGRATION_TROUBLESHOOTING.md) for more details.

## Development Guidelines

- Follow PEP 8 style guidelines
- Write docstrings for all functions and classes
- Use English for all code comments and variable names
- Always use English logical operators (`and`, `or`) instead of Arabic ones (و, أو)
- Run tests before submitting changes

## License

Copyright © 2025 - All rights reserved
