# Migration Troubleshooting Guide

This guide explains how to troubleshoot and resolve common database migration issues in Flask applications using Alembic.

## Multiple Head Revisions Issue

### What is it?

When you see an error like:
```
Error: Multiple head revisions are present for given argument 'head'; please specify a specific target revision
```

This means your database migration history has multiple branches (heads) that need to be merged before you can proceed.

### How to Fix It

#### Option 1: Using the Fix Scripts

We've provided two scripts to help resolve this issue:

1. **Automatic Fix**:
   ```bash
   python fix_migrations.py
   ```
   This script automatically detects multiple heads and creates a merge migration.

2. **Interactive Fix**:
   ```bash
   python fix_migrations_interactive.py
   ```
   This script guides you through the fixing process with interactive prompts.

#### Option 2: Manual Resolution

If you prefer to fix the issue manually:

1. First, identify the multiple heads:
   ```bash
   flask db heads
   ```

2. Create a merge migration:
   ```bash
   flask db merge <revision1> <revision2> -m "merge multiple heads"
   ```

3. Apply the merge:
   ```bash
   flask db upgrade
   ```

## Other Common Migration Issues

### "Can't locate revision identified by..."

This usually means your alembic_version table contains a revision ID that doesn't exist in your migrations folder.

To fix:
1. Check your current revision:
   ```bash
   flask db current
   ```

2. Stamp the database with a known good revision:
   ```bash
   flask db stamp <revision_id>
   ```

3. Then upgrade:
   ```bash
   flask db upgrade
   ```

### "Database is not up to date"

This means there are pending migrations that need to be applied.

To fix:
```bash
flask db upgrade
```

If that fails, you may need to:
1. Identify what revision your database is at:
   ```bash
   flask db current
   ```
   
2. Stamp the database with the latest revision:
   ```bash
   flask db stamp head
   ```

### "Target database is not up to date"

This usually happens when you try to create a new migration but your database has unapplied migrations.

To fix:
```bash
flask db upgrade
flask db migrate -m "your message"
```

## Complete Database Reset (Last Resort)

If all else fails, you can completely reset your migration state:

1. Back up your database!

2. Delete or rename your database file (if using SQLite).

3. Delete the migrations folder.

4. Re-initialize migrations:
   ```bash
   flask db init
   flask db migrate -m "initial migration"
   flask db upgrade
   ```

## Prevention Tips

1. Always run `flask db upgrade` after pulling code with new migrations.
2. Create proper merges when working on multiple branches.
3. Commit your migration files along with code changes.
4. Use descriptive migration messages with `-m` flag.
