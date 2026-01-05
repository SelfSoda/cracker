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
    market: Optional[str] = Field(None, description="交易市场（如：A股、场内、场外等）")
    broker: Optional[str] = Field(None, description="券商/交易平台（如：华泰证券、支付宝、天天基金等）")
    account: Optional[str] = Field(None, description="交易账户标识（如有多个账户）")
    order_id: Optional[str] = Field(None, description="交易单号/订单号（用于对账）")
    notes: Optional[str] = Field("", description="备注信息")


class InvestmentRecordCreate(InvestmentRecordBase):
    """创建投资记录的schema"""
    pass


class InvestmentRecordUpdate(BaseModel):
    """更新投资记录的schema"""
    symbol: Optional[str] = None
    name: Optional[str] = None
    investment_type: Optional[InvestmentType] = None
    transaction_type: Optional[TransactionType] = None
    quantity: Optional[float] = Field(None, gt=0)
    price: Optional[float] = Field(None, gt=0)
    amount: Optional[float] = None
    transaction_date: Optional[datetime] = None
    fee: Optional[float] = Field(None, ge=0)
    tax: Optional[float] = Field(None, ge=0)
    market: Optional[str] = None
    broker: Optional[str] = None
    account: Optional[str] = None
    order_id: Optional[str] = None
    notes: Optional[str] = None


class InvestmentRecordResponse(InvestmentRecordBase):
    """投资记录响应schema"""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


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


class PortfolioSummary(BaseModel):
    """投资组合摘要"""
    total_cost: float = Field(..., description="总成本")
    total_value: float = Field(..., description="总市值")
    total_profit_loss: float = Field(..., description="总盈亏")
    total_profit_loss_rate: float = Field(..., description="总盈亏率")
    positions: List[PositionSummary] = Field(..., description="持仓列表")

