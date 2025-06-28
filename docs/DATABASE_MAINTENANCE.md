# Database Maintenance Guide

This guide covers common database maintenance tasks and how to resolve issues with the project management system database.

## Regular Maintenance

### 1. Backup Database

Always back up your database before any maintenance operation:

```bash
# The db_fix.py script automatically creates backups, but you can also:
cp instance/site.db instance/site.db.backup
```

### 2. Verify Database Integrity

Use the verification script to check database integrity:

```bash
python verify_db.py
```

This script checks for:
- Table existence
- Record counts
- Relationship integrity
- Essential data presence

### 3. Run Migrations

When there are schema changes, apply them with:

```bash
flask db migrate -m "Description of changes"
flask db upgrade
```

## Troubleshooting

### Common Problems and Solutions

#### "Entity namespace for X has no property Y"

This typically indicates a relationship issue. To fix:

1. Run the database fix script:
   ```bash
   python db_fix.py
   ```

2. If the error persists, check the model definitions in `app/models.py`.

#### "no such column" Errors

If you see errors about missing columns:

1. Run a full database upgrade:
   ```bash
   flask db upgrade
   ```

2. If issues persist, you may need to recreate the database:
   ```bash
   rm instance/site.db
   flask db upgrade
   python db_fix.py
   ```

#### "Constraint must have a name"

This error occurs with unnamed constraints. To fix:

1. Ensure your SQLAlchemy metadata has naming conventions:
   ```python
   # In app/__init__.py or config.py
   naming_convention = {
       "ix": "ix_%(column_0_label)s",
       "uq": "uq_%(table_name)s_%(column_0_name)s",
       "ck": "ck_%(table_name)s_%(constraint_name)s",
       "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
       "pk": "pk_%(table_name)s"
   }
   metadata = MetaData(naming_convention=naming_convention)
   db = SQLAlchemy(metadata=metadata)
   ```

2. Re-run migrations with:
   ```bash
   flask db migrate -m "Add naming conventions"
   flask db upgrade
   ```

## Database Schema

The core database schema consists of:

- `user`: System users
- `department`: Organizational departments
- `project`: Projects within the system
- `task`: Tasks belonging to projects
- `time_entry`: Time records for tasks/projects
- `risk_assessment`: Project risk assessments

Refer to `app/models.py` for the complete schema definition.

## Arabic Operators Warning

During development, ensure all logical operators are in English. The system includes a scanner to detect Arabic operators:

```bash
python scan_arabic_operators.py
```

Replace any found instances of:
- Arabic "و" with English "and"
- Arabic "أو" with English "or"
