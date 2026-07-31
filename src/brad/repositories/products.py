from __future__ import annotations

from collections.abc import Sequence
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from brad.core.models.operational import (
    FinancialProduct,
    ProductHolder,
    ProductTransaction,
    ProductValue,
)
from brad.repositories.base import BaseRepository


class ProductRepository(BaseRepository[FinancialProduct]):
    def __init__(self, session: Session):
        super().__init__(session, FinancialProduct)

    def get_active(self) -> Sequence[FinancialProduct]:
        """Return all active financial products."""
        stmt = select(FinancialProduct).where(FinancialProduct.is_active.is_(True))
        return self.session.scalars(stmt).all()

    def list_all_with_types(self) -> Sequence[FinancialProduct]:
        """Return all financial products with type relationship eager-loaded."""
        stmt = select(FinancialProduct).options(joinedload(FinancialProduct.type_link))
        return self.session.scalars(stmt).unique().all()

    def set_holders(self, product: FinancialProduct, holder_ids: list[int]) -> None:
        """Set holders for a product (replaces existing)."""
        new_links = []
        for ordinal, holder_id in enumerate(holder_ids, start=1):
            new_links.append(
                ProductHolder(
                    product_id=product.id,
                    holder_id=holder_id,
                    ordinal=ordinal,
                )
            )
        product.holder_links = new_links
        self.session.flush()


class ProductValueRepository(BaseRepository[ProductValue]):
    def __init__(self, session: Session):
        super().__init__(session, ProductValue)

    def get_latest(self, product_id: int) -> ProductValue | None:
        """Get the most recent valuation for a product."""
        stmt = (
            select(ProductValue)
            .where(ProductValue.product_id == product_id)
            .order_by(ProductValue.date.desc())
            .limit(1)
        )
        return self.session.scalars(stmt).first()

    def get_latest_before(
        self, product_id: int, before_date: date
    ) -> ProductValue | None:
        """Get the most recent valuation for a product before a given date."""
        stmt = (
            select(ProductValue)
            .where(
                ProductValue.product_id == product_id,
                ProductValue.date < before_date,
            )
            .order_by(ProductValue.date.desc())
            .limit(1)
        )
        return self.session.scalars(stmt).first()


class ProductTransactionRepository(BaseRepository[ProductTransaction]):
    def __init__(self, session: Session):
        super().__init__(session, ProductTransaction)

    def get_by_product(self, product_id: int) -> Sequence[ProductTransaction]:
        """Get all transactions for a product."""
        stmt = (
            select(ProductTransaction)
            .where(ProductTransaction.product_id == product_id)
            .order_by(ProductTransaction.date.desc())
        )
        return self.session.scalars(stmt).all()
