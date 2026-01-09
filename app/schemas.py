"""Pydantic schemas for API request/response"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from app.models import InvestmentType, TransactionType


class InvestmentRecordBase(BaseModel):
    """投资记录基础schema"""
    symbol: str = Field(..., description="投资标的代码，如股票代码、基金代码")
    name: str = Field(..., description="投资标的名称")
    investment_type: InvestmentType = Field(..., description="投资类型：股票/基金/债券/其他")
    transaction_type: TransactionType = Field(..., description="交易类型：买入/卖出")
    quantity: float = Field(..., gt=0, description="交易数量（股数/份数等）")
    price: float = Field(..., gt=0, description="交易价格（股价/基金净值等）")
    amount: float = Field(..., description="交易金额（quantity * price）")
    transaction_date: datetime = Field(..., description="交易日期时间")
    fee: float = Field(0.0, ge=0, description="手续费/佣金")
    tax: Optional[float] = Field(0.0, ge=0, description="税费（印花税、过户费等）")
    broker: Optional[str] = Field(None, description="券商/交易平台（如：华泰证券、支付宝、天天基金等）")
    account: Optional[str] = Field(None, description="交易账户标识（如有多个账户）")
    order_id: Optional[str] = Field(None, description="交易单号/订单号（用于对账）")
    notes: Optional[str] = Field("", description="备注信息")


class PositionSummary(BaseModel):
    """持仓摘要"""
    symbol: str
    name: str
    investment_type: InvestmentType
    total_quantity: float = Field(..., description="总持仓数量")
    average_cost: float = Field(..., description="平均成本")
    total_cost: float = Field(..., description="总成本")
    current_price: Optional[float] = Field(None, description="当前价格")
    current_value: Optional[float] = Field(None, description="当前市值")
    profit_loss: Optional[float] = Field(None, description="盈亏")
    profit_loss_rate: Optional[float] = Field(None, description="盈亏率")


class PriceData(BaseModel):
    """价格数据"""
    symbol: str
    price: float
    date: datetime
