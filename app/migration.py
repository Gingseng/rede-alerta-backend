"""Small additive schema upgrade for installations created before social posting."""

def ensure_schema(engine):
    """Create new tables through metadata and leave existing case data untouched.

    The social publication state lives in a new table, so this migration is safe
    for both existing SQLite development databases and Render Postgres databases.
    """
    # Importing models registers the table on Base.metadata before create_all.
    from .database import Base
    from . import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
