from typing import Generic, Sequence, TypeVar

from sqlalchemy import select
from sqlalchemy.orm import Session

from brad.core.models.base import Base

T = TypeVar("T", bound=Base)


class BaseRepository(Generic[T]):
    """Base repository providing common CRUD operations."""

    def __init__(self, session: Session, model: type[T]):
        self.session = session
        self.model = model

    def create(self, entity: T) -> T:
        """Add a new entity to the session."""
        self.session.add(entity)
        self.session.flush()
        return entity

    def create_many(self, entities: list[T]) -> list[T]:
        """Add multiple entities to the session."""
        self.session.add_all(entities)
        self.session.flush()
        return entities

    def get_by_id(self, entity_id: int) -> T | None:
        """Get an entity by its primary key."""
        return self.session.get(self.model, entity_id)

    def get_by_name(self, name: str) -> T | None:
        """Get an entity by its name (assumes a 'name' column exists)."""
        stmt = select(self.model).where(self.model.name == name)
        return self.session.scalars(stmt).first()

    def list_all(self) -> Sequence[T]:
        """Return all entities."""
        stmt = select(self.model)
        return self.session.scalars(stmt).all()

    def delete(self, entity: T) -> None:
        """Remove an entity from the session."""
        self.session.delete(entity)
        self.session.flush()
