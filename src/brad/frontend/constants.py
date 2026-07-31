class StateKeys:
    """Streamlit session state keys."""

    SESSION_FACTORY = "session_factory"
    BALANCE_BATCH = "balance_batch"
    VALUATION_BATCH = "valuation_batch"
    NAVIGATION_PAGE = "navigation_page"
    NAV_TO = "nav_to"
    ENTITY_TAB = "entity_tab"


class Pages:
    """Application navigation page names."""

    ADD_BALANCE = "Add Balance"
    ADD_VALUATION = "Add Valuation"
    MANAGE_ENTITIES = "Manage Entities"

    @classmethod
    def list_all(cls) -> list[str]:
        return [cls.ADD_BALANCE, cls.ADD_VALUATION, cls.MANAGE_ENTITIES]


class EntityTabs:
    """Entity management tab names."""

    PROVIDERS = "Providers"
    HOLDERS = "Holders"
    ACCOUNTS = "Accounts"
    FINANCIAL_PRODUCTS = "Financial Products"

    @classmethod
    def list_all(cls) -> list[str]:
        return [cls.PROVIDERS, cls.HOLDERS, cls.ACCOUNTS, cls.FINANCIAL_PRODUCTS]
