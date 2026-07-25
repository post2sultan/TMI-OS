"""Reserved API module for the versioned generation router.

The active legacy-compatible route remains registered in ``app.main`` during
foundation migration. Keeping this module valid prevents package compilation
failures while the API is moved to ``/api/v1`` in the next release gate.
"""
