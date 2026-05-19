from sqlalchemy import Column, Integer, String, Numeric
from database import Base
from decimal import Decimal

class Bank(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String(100), nullable=False)

    balance = Column(
        Numeric(10, 2),
        nullable=False,
        default=Decimal("0.00")
    )