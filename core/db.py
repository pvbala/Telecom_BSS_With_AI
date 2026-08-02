"""
Single shared database engine/session for the whole modular monolith.

IMPORTANT (additive-data guarantee):
- init_db() only calls Base.metadata.create_all(), which creates tables
  that don't yet exist and NEVER drops or truncates existing tables/rows.
- No module in this codebase should ever call drop_all() or DELETE FROM
  without an explicit, separate "reset" command run intentionally by a
  human. Test data generation always ADDS new rows on top of what exists.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from contextlib import contextmanager

from core.config import DATABASE_URL

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

Base = declarative_base()


def init_db():
    """Create any missing tables. Never touches existing data."""
    # Import all module models so they register with Base.metadata
    from modules.party import models as _party_models          # noqa
    from modules.catalog import models as _catalog_models       # noqa
    from modules.order import models as _order_models           # noqa
    from modules.inventory import models as _inventory_models   # noqa
    from modules.mediation_rating import models as _mediation_models  # noqa
    from modules.billing import models as _billing_models       # noqa
    from modules.assurance import models as _assurance_models   # noqa
    from modules.crm import models as _crm_models                # noqa
    from modules.resource_inventory import models as _resource_models  # noqa
    from ai_ml import model_registry as _model_registry          # noqa

    Base.metadata.create_all(bind=engine)


@contextmanager
def get_session():
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def next_sequence_number(session, model, code_column: str) -> int:
    """
    Additive-safe sequence helper: counts EXISTING rows and returns the
    next number, so newly generated test data continues on from whatever
    is already in the database rather than restarting at 1.
    """
    existing = session.query(model).count()
    return existing + 1