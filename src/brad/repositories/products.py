from datetime import date
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

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
        stmt = select(FinancialProduct).where(
            FinancialProduct.is_active.is_(True)
        )
        return self.session.scalars(stmt).all()

    def set_holders(
        self, product: FinancialProduct, holder_ids: list[int]
    ) -> None:
        """Set holders for a product (replaces existing)."""
        product.holder_links.clear()
        self.session.flush()
        for ordinal, holder_id in enumerate(holder_ids, start=1):
            link = ProductHolder(
                product_id=product.id,
                holder_id=holder_id,
                ordinal=ordinal,
            )
            self.session.add(link)
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


class ProductTransactionRepository(BaseRepository[ProductTransaction]):
    def __init__(self, session: Session):
        super().__init__(session, ProductTransaction)

    def get_by_product(
        self, product_id: int
    ) -> Sequence[ProductTransaction]:
        """Get all transactions for a product."""
        stmt = (
            select(ProductTransaction)
            .where(ProductTransaction.product_id == product_id)
            .order_by(ProductTransaction.date.desc())
        )
        return self.session.scalars(stmt).all()
