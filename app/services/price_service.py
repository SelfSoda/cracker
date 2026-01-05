"""价格获取服务，使用akshare获取实时价格"""
import akshare as ak
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from loguru import logger

from app.models import PriceHistory, InvestmentType


class PriceService:
    """价格服务类"""

    @staticmethod
    def get_stock_price(symbol: str) -> Optional[float]:
        """获取股票实时价格"""
        try:
            # akshare获取股票实时行情
            # stock_zh_a_spot_em()返回的"代码"列是6位数字，不带前缀
            # 如果用户输入带前缀，先去掉前缀
            clean_symbol = symbol
            if symbol.startswith(("sh", "sz", "bj")):
                clean_symbol = symbol[2:]
            
            df = ak.stock_zh_a_spot_em()
            if df.empty:
                logger.warning("无法获取股票行情数据")
                return None
            
            # 尝试精确匹配
            stock_info = df[df["代码"] == clean_symbol]
            if not stock_info.empty:
                return float(stock_info.iloc[0]["最新价"])
            
            # 如果精确匹配失败，尝试包含前缀的匹配
            if symbol != clean_symbol:
                stock_info = df[df["代码"] == symbol]
                if not stock_info.empty:
                    return float(stock_info.iloc[0]["最新价"])
            
            logger.warning(f"无法找到股票代码 {symbol} (尝试了 {clean_symbol})")
            return None
        except Exception as e:
            logger.error(f"获取股票价格失败 {symbol}: {str(e)}")
            return None

    @staticmethod
    def get_fund_price(symbol: str) -> Optional[float]:
        """获取基金实时价格（净值）"""
        try:
            # akshare获取基金实时净值
            df = ak.fund_etf_hist_sina(symbol=symbol)
            if not df.empty:
                return float(df.iloc[-1]["净值"])
            logger.warning(f"无法获取基金 {symbol} 的价格")
            return None
        except Exception as e:
            logger.error(f"获取基金价格失败 {symbol}: {str(e)}")
            return None

    @staticmethod
    def get_price(symbol: str, investment_type: InvestmentType) -> Optional[float]:
        """根据投资类型获取价格"""
        if investment_type == InvestmentType.STOCK:
            return PriceService.get_stock_price(symbol)
        elif investment_type == InvestmentType.FUND:
            return PriceService.get_fund_price(symbol)
        else:
            logger.warning(f"暂不支持的投资类型: {investment_type}")
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

