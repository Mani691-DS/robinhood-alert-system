import os
import sys
from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel
from sqlalchemy import Boolean, Column, DateTime, Integer, Numeric, String, func

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from shared.base import Base


# ── SQLAlchemy ORM model ──────────────────────────────────────────────────────

class Alert(Base):
    __tablename__ = "alerts"

    id              = Column(Integer, primary_key=True, autoincrement=True)
    user_phone      = Column(String(20), nullable=False)
    ticker          = Column(String(10), nullable=False)
    threshold_price = Column(Numeric(10, 2), nullable=False)
    direction       = Column(String(5), nullable=False)   # 'above' or 'below'
    is_active       = Column(Boolean, default=True, nullable=False)
    created_at      = Column(DateTime(timezone=True), server_default=func.now())


# ── Pydantic schemas ──────────────────────────────────────────────────────────

class AlertCreate(BaseModel):
    user_phone:      str
    ticker:          str
    threshold_price: Decimal
    direction:       Literal["above", "below"]


class AlertResponse(BaseModel):
    id:              int
    user_phone:      str
    ticker:          str
    threshold_price: Decimal
    direction:       str
    is_active:       bool
    created_at:      datetime

    class Config:
        from_attributes = True
