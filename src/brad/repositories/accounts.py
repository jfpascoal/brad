from __future__ import annotations

from collections.abc import Sequence
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from brad.core.models.operational import (
    Account,
    AccountBalance,
    AccountHolder,
    AccountTransaction,
)
from brad.repositories.base import BaseRepository


class AccountRepository(BaseRepository[Account]):
    def __init__(self, session: Session):
        super().__init__(session, Account)

    def get_active(self) -> Sequence[Account]:
        """Return all active accounts."""
        stmt = select(Account).where(Account.is_active.is_(True))
        return self.session.scalars(stmt).all()

    def list_all_with_types(self) -> Sequence[Account]:
        """Return all accounts with type relationship eager-loaded."""
        stmt = select(Account).options(joinedload(Account.type_link))
        return self.session.scalars(stmt).unique().all()

    def set_holders(self, account: Account, holder_ids: list[int]) -> None:
        """Set holders for an account (replaces existing)."""
        new_links = []
        for ordinal, holder_id in enumerate(holder_ids, start=1):
            new_links.append(
                AccountHolder(
                    account_id=account.id,
                    holder_id=holder_id,
                    ordinal=ordinal,
                )
            )
        account.holder_links = new_links
        self.session.flush()


class AccountBalanceRepository(BaseRepository[AccountBalance]):
    def __init__(self, session: Session):
        super().__init__(session, AccountBalance)

    def get_latest(self, account_id: int) -> AccountBalance | None:
        """Get the most recent balance for an account."""
        stmt = (
            select(AccountBalance)
            .where(AccountBalance.account_id == account_id)
            .order_by(AccountBalance.date.desc())
            .limit(1)
        )
        return self.session.scalars(stmt).first()

    def get_by_date_range(
        self, account_id: int, start: date, end: date
    ) -> Sequence[AccountBalance]:
        """Get balances within a date range."""
        stmt = (
            select(AccountBalance)
            .where(
                AccountBalance.account_id == account_id,
                AccountBalance.date >= start,
                AccountBalance.date <= end,
            )
            .order_by(AccountBalance.date)
        )
        return self.session.scalars(stmt).all()


class AccountTransactionRepository(BaseRepository[AccountTransaction]):
    def __init__(self, session: Session):
        super().__init__(session, AccountTransaction)

    def get_by_account(self, account_id: int) -> Sequence[AccountTransaction]:
        """Get all transactions for an account."""
        stmt = (
            select(AccountTransaction)
            .where(AccountTransaction.account_id == account_id)
            .order_by(AccountTransaction.date.desc())
        )
        return self.session.scalars(stmt).all()
