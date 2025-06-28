# Database Migration Structure

## Current Issue: Multiple Heads

Your database migration history has diverged, leading to multiple "heads" that need to be merged:

```
Migration History (before fix):

                        ┌──────────────────┐
                        │ Initial Migration │
                        └─────────┬────────┘
                                  │
                        ┌─────────▼────────┐
                        │ Some migrations   │
                        └─────────┬────────┘
                                  │
                   ┌──────────────┴──────────────┐
                   │                             │
        ┌──────────▼─────────┐       ┌──────────▼────────────┐
HEAD 1: │ 3b5c2a9f8123       │       │ Other migration branch │ :HEAD 2
        │ Add timezone field  │       │                       │
        └──────────┬─────────┘       └───────────────────────┘
                   │
        ┌──────────▼─────────┐
        │ 4d2c7a5b8123       │
        │ Add primary_color  │
        └────────────────────┘
```

## After Fix (Target Structure)

After running the fix script, your migration history will look like this:

```
Migration History (after fix):

                        ┌──────────────────┐
                        │ Initial Migration │
                        └─────────┬────────┘
                                  │
                        ┌─────────▼────────┐
                        │ Some migrations   │
                        └─────────┬────────┘
                                  │
                   ┌──────────────┴──────────────┐
                   │                             │
        ┌──────────▼─────────┐       ┌──────────▼────────────┐
        │ 3b5c2a9f8123       │       │ Other migration branch │
        │ Add timezone field  │       │                       │
        └──────────┬─────────┘       └───────────┬───────────┘
                   │                             │
        ┌──────────▼─────────┐                   │
        │ 4d2c7a5b8123       │                   │
        │ Add primary_color  │                   │
        └──────────┬─────────┘                   │
                   │                             │
                   └─────────────┬───────────────┘
                                 │
                      ┌──────────▼─────────┐
                      │ Merge Migration    │ :SINGLE HEAD
                      │ (auto-generated)   │
                      └────────────────────┘
```

This merged structure allows you to continue creating new migrations without conflicts.
