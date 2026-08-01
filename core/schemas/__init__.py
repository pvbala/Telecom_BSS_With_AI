from pydantic import BaseModel, ConfigDict


class ORMBase(BaseModel):
    """Base for any Pydantic model that reads from a SQLAlchemy ORM object."""
    model_config = ConfigDict(from_attributes=True)
