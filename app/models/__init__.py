"""Import all models so Alembic and db.create_all() can find them."""
from app.models.user import User  # noqa: F401
from app.models.chore import Chore, ChoreHistory  # noqa: F401
from app.models.grocery import GroceryItem  # noqa: F401
from app.models.security import TrustedIP, PinAttempt, AppConfig  # noqa: F401
from app.models.calendar import CalendarEvent  # noqa: F401
from app.models.bank import BankAccount, SavingsDeposit, Transaction, SavingsGoal  # noqa: F401
from app.models.mission import Mission, MissionAssignment, MissionProgress  # noqa: F401
from app.models.achievement import Achievement, UserAchievement  # noqa: F401
from app.models.lifestyle import (  # noqa: F401
    LifestyleGoal,
    LifestyleLog,
    LifestylePrivilege,
    LifestyleRedemption,
)
