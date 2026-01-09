"""价格获取服务，使用akshare获取实时价格"""
import akshare as ak
from datetime import datetime, date
from typing import Optional, Literal
from sqlalchemy.orm import Session
from loguru import logger
import pandas as pd

from app.models import PriceHistory, InvestmentType


class PriceService:
    """价格服务类"""

    @staticmethod
    def get_stock_price_by_date(symbol: str, date_str: str) -> float | None:
        """获取股票实时价格"""
        df = ak.stock_zh_a_hist(symbol=symbol, period="daily", start_date=date_str, end_date=date_str)
        if df.empty:
            logger.warning(f"无法获取{date_str}股票行情数据: {symbol}")
            return None
        price = df.at[0, "收盘"]
        return price

    @staticmethod
    def get_fund_price(symbol: str) -> float | None:
        """获取公募基金实时价格（净值）"""
        try:
            # 尝试使用公募基金净值接口
            try:
                # fund_open_fund_info_em 获取基金净值走势
                df = ak.fund_open_fund_info_em(fund=symbol, indicator="单位净值走势")
                if not df.empty and "净值" in df.columns:
                    return float(df.iloc[-1]["净值"])
            except Exception:
                pass

            # 如果上面失败，尝试 ETF 接口（用于场内基金）
            try:
                df = ak.fund_etf_hist_sina(symbol=symbol)
                if not df.empty and "净值" in df.columns:
                    return float(df.iloc[-1]["净值"])
            except Exception:
                pass

            logger.warning(f"无法获取基金 {symbol} 的价格")
            return None
        except Exception as e:
            logger.error(f"获取基金价格失败 {symbol}: {str(e)}")
            return None

    @staticmethod
    def get_precious_metal_price(symbol: Literal["黄金", "白银"]) -> float | None:
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

    @staticmethod
    def get_price(symbol: str, investment_type: InvestmentType) -> Optional[float]:
        """根据投资类型获取价格"""
        if investment_type == InvestmentType.STOCK:
            return PriceService.get_stock_price(symbol)
        elif investment_type == InvestmentType.FUND:
            return PriceService.get_fund_price(symbol)
        elif investment_type == InvestmentType.PRECIOUS_METAL:
            return PriceService.get_precious_metal_price(symbol)
        else:
            logger.warning(f"暂不支持的投资类型: {investment_type}")
            return None

    @staticmethod
    def get_stock_history(
            symbol: str,
            start_date: Optional[str] = None,
            end_date: Optional[str] = None,
            adjust: str = "qfq"
    ) -> Optional[pd.DataFrame]:
        """获取股票历史价格数据
        
        Args:
            symbol: 股票代码
            start_date: 开始日期，格式 'YYYYMMDD'
            end_date: 结束日期，格式 'YYYYMMDD'
            adjust: 复权类型，'qfq'前复权，'hfq'后复权，''不复权
        """
        try:
            clean_symbol = symbol
            if symbol.startswith(("sh", "sz", "bj")):
                clean_symbol = symbol[2:]

            df = ak.stock_zh_a_hist(
                symbol=clean_symbol,
                period="daily",
                start_date=start_date,
                end_date=end_date,
                adjust=adjust
            )
            return df
        except Exception as e:
            logger.error(f"获取股票历史价格失败 {symbol}: {str(e)}")
            return None

    @staticmethod
    def get_fund_history(
            symbol: str,
            indicator: str = "单位净值走势"
    ) -> Optional[pd.DataFrame]:
        """获取基金历史净值数据
        
        Args:
            symbol: 基金代码
            indicator: 指标类型，'单位净值走势' 或 '累计净值走势'
        """
        try:
            df = ak.fund_open_fund_info_em(fund=symbol, indicator=indicator)
            return df
        except Exception as e:
            logger.error(f"获取基金历史净值失败 {symbol}: {str(e)}")
            return None

    @staticmethod
    def get_precious_metal_history(
            symbol: str,
            start_date: Optional[str] = None,
            end_date: Optional[str] = None
    ) -> Optional[pd.DataFrame]:
        """获取贵金属历史价格数据
        
        Args:
            symbol: 贵金属代码
            start_date: 开始日期，格式 'YYYYMMDD'
            end_date: 结束日期，格式 'YYYYMMDD'
        """
        try:
            # 贵金属历史数据可能需要使用不同的接口
            # 这里提供一个基础实现，可能需要根据实际接口调整
            metal_map = {
                "黄金": "黄金",
                "gold": "黄金",
                "au": "黄金",
                "AU": "黄金",
            }
            metal_name = metal_map.get(symbol.lower() if isinstance(symbol, str) else symbol, symbol)

            # 尝试获取历史数据（具体接口可能需要根据 akshare 版本调整）
            # 这里先返回 None，后续可以根据实际需求实现
            logger.warning(f"贵金属历史价格获取功能待完善: {symbol}")
            return None
        except Exception as e:
            logger.error(f"获取贵金属历史价格失败 {symbol}: {str(e)}")
            return None

    @staticmethod
    def get_price_with_cache(
            db: Session, symbol: str, investment_type: InvestmentType
    ) -> Optional[float]:
        """获取价格，优先从缓存读取，如果缓存没有或过期则从akshare获取"""
        # 查询最近的价格记录（1小时内）
        from datetime import timedelta
        cutoff_time = datetime.now() - timedelta(hours=1)

        cached_price = (
            db.query(PriceHistory)
            .filter(
                PriceHistory.symbol == symbol,
                PriceHistory.date >= cutoff_time
            )
            .order_by(PriceHistory.date.desc())
            .first()
        )

        if cached_price:
            return cached_price.price

        # 从akshare获取最新价格
        price = PriceService.get_price(symbol, investment_type)

        if price is not None:
            # 保存到缓存
            price_history = PriceHistory(
                symbol=symbol,
                price=price,
                date=datetime.now()
            )
            db.add(price_history)
            db.commit()

        return price
