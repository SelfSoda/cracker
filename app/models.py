"""数据库模型"""
import enum

from sqlalchemy import Column, Integer, String, Float, DateTime, Date, Enum as SQLEnum
from sqlalchemy.sql import func

from app.database import Base


class InvestmentType(str, enum.Enum):
    """投资类型枚举"""
    STOCK = "stock"  # 股票
    FUND = "fund"  # 基金
    PRECIOUS_METAL = "precious_metal"  # 贵金属


class TransactionType(str, enum.Enum):
    """交易类型枚举"""
    BUY = "buy"  # 买入
    SELL = "sell"  # 卖出


class InvestmentRecord(Base):
    """投资记录表"""
    __tablename__ = "investment_records"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True, nullable=False, comment="投资标的代码，如股票代码、基金代码")
    name = Column(String, nullable=False, comment="投资标的名称")
    investment_type = Column(SQLEnum(InvestmentType), nullable=False, comment="投资类型")
    transaction_type = Column(SQLEnum(TransactionType), nullable=False, comment="交易类型")
    quantity = Column(Float, nullable=False, comment="交易数量")
    price = Column(Float, nullable=False, comment="交易价格")
    amount = Column(Float, nullable=False, comment="交易金额")
    transaction_date = Column(Date, nullable=False, index=True, comment="交易日期时间")
    fee = Column(Float, default=0.0, comment="手续费/佣金")
    tax = Column(Float, default=0.0, comment="税费（印花税、过户费等）")
    broker = Column(String, nullable=True, comment="券商/交易平台（如：华泰证券、支付宝、天天基金等）")
    account = Column(String, nullable=True, comment="交易账户标识（如有多个账户）")
    order_id = Column(String, nullable=True, index=True, comment="交易单号/订单号（用于对账）")
    notes = Column(String, default="", comment="备注信息")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")


class PriceHistory(Base):
    """价格历史表，用于缓存和记录历史价格"""
    __tablename__ = "price_history"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True, nullable=False, comment="投资标的代码")
    price = Column(Float, nullable=False, comment="价格")
    date = Column(Date, nullable=False, index=True, comment="价格日期")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
