# Migration Fix Steps

Follow these steps in order to fix the "Multiple head revisions" error:

## Step 1: Run the fix_migrations.py script

```bash
python fix_migrations.py
```

This script will automatically detect and merge multiple migration heads.

## Step 2: Upgrade the database

After the merge migration is created, upgrade the database:

```bash
flask db upgrade
```

## Step 3: Verify the database is up to date

Check that the database is now up to date:

```bash
flask db current
```

You should see a single current revision, not multiple heads.

## Step 4: Create a new migration if needed

Now you can create a new migration for any additional changes:

```bash
flask db migrate -m "Description of changes"
flask db upgrade
```

## Troubleshooting

If the automatic fix doesn't work, try the interactive version:

```bash
python fix_migrations_interactive.py
```

This will guide you through the process with options for how to handle the multiple heads.

## Manual Fix (if scripts don't work)

You can also fix this manually:

1. Identify the heads:
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
