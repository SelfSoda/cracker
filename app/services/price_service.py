"""价格获取服务，使用akshare获取实时价格"""
import akshare as ak
from datetime import datetime
from typing import Optional, Literal
from sqlalchemy.orm import Session
from loguru import logger
import pandas as pd

from app.models import PriceHistory, InvestmentType


def _get_stock_price(symbol: str, date_str: str | None = None) -> float | None:
    """获取股票实时价格"""
    date_str = date_str or datetime.now().strftime("%Y%m%d")
    df = ak.stock_zh_a_hist(symbol=symbol, period="daily", start_date=date_str, end_date=date_str)
    if df.empty:
        logger.warning(f"无法获取{date_str}股票行情数据: {symbol}")
        return None
    price = df.at[0, "收盘"]
    return price


def _get_fund_price(symbol: str) -> float | None:
    """获取公募基金实时价格（净值）"""
    df = ak.fund_open_fund_info_em(symbol=symbol, indicator="单位净值走势")
    if df.empty:
        logger.warning(f"无法获取基金行情数据: {symbol}")
        return None
    price = df.at[df.index[-1], "单位净值"]
    return price


def _get_precious_metal_price(symbol: Literal["黄金", "白银"]) -> float | None:
    """获取贵金属实时价格"""
    if symbol == "黄金":
        symbol = "Au99.99"
    elif symbol == "白银":
        symbol = "Ag99.99"
    else:
        logger.warning(f"贵金属只支持'黄金'或'白银': {symbol}")
        return None

    df = ak.spot_quotations_sge(symbol=symbol)
    if df.empty:
        logger.warning(f"无法获取{symbol}行情数据")
        return None
    price = df.at[df.index[-1], "现价"]
    return price


def _get_price(symbol: str, investment_type: InvestmentType) -> Optional[float]:
    """根据投资类型获取价格"""
    if investment_type == InvestmentType.STOCK:
        return _get_stock_price(symbol)
    elif investment_type == InvestmentType.FUND:
        return _get_fund_price(symbol)
    elif investment_type == InvestmentType.PRECIOUS_METAL:
        return _get_precious_metal_price(symbol)
    else:
        logger.warning(f"暂不支持的投资类型: {investment_type}")
        return None


def update_price(
        db: Session, symbol: str, investment_type: InvestmentType
) -> float | None:
    """获取价格，优先从缓存读取，如果缓存没有或过期则从akshare获取"""
    # 查询最近的价格记录（1小时内）
    from datetime import timedelta
    now = datetime.now()

    price_from_db = (
        db.query(PriceHistory)
        .filter(
            PriceHistory.symbol == symbol,
            PriceHistory.date >= now.date(),
        )
        .order_by(PriceHistory.date.desc())
        .first()
    )

    if price_from_db:
        return price_from_db.price

    # 从akshare获取最新价格
    price = _get_price(symbol, investment_type)

    if price is not None:
        # 保存到缓存
        price_history = PriceHistory(
            symbol=symbol,
            price=price,
            date=now.date(),
        )
        db.add(price_history)
        db.commit()

    return price
