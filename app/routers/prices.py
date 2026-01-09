"""价格相关的API路由"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime
import pandas as pd

from app.database import get_db
from app.models import InvestmentType
from app.schemas import (
    PriceData, 
    HistoricalPriceResponse, 
    HistoricalPriceData,
    BatchPriceRequest,
    BatchPriceResponse
)
from app.services.price_service import PriceService

router = APIRouter(prefix="/api/prices", tags=["prices"])


@router.get("/{symbol}", response_model=PriceData)
def get_price(
    symbol: str,
    investment_type: InvestmentType,
    db: Session = Depends(get_db)
):
    """
    获取指定标的的当前价格
    
    - **symbol**: 标的代码（如股票代码 600519、基金代码 000001、贵金属 黄金）
    - **investment_type**: 投资类型（stock/fund/precious_metal）
    
    支持的投资类型：
    - **stock**: A股股票（如 600519、000001、sz000001）
    - **fund**: 公募基金（如 000001、159919）
    - **precious_metal**: 贵金属（如 黄金、白银、AU、AG）
    """
    price = PriceService.get_price_with_cache(db, symbol, investment_type)
    
    if price is None:
        raise HTTPException(
            status_code=404,
            detail=f"无法获取 {symbol} ({investment_type.value}) 的价格，请检查代码是否正确"
        )
    
    return PriceData(
        symbol=symbol,
        price=price,
        date=datetime.now()
    )


@router.get("/{symbol}/history", response_model=HistoricalPriceResponse)
def get_price_history(
    symbol: str,
    investment_type: InvestmentType,
    start_date: Optional[str] = Query(None, description="开始日期，格式：YYYYMMDD"),
    end_date: Optional[str] = Query(None, description="结束日期，格式：YYYYMMDD"),
    adjust: str = Query("qfq", description="复权类型（仅股票有效）：qfq前复权、hfq后复权、空字符串不复权"),
    db: Session = Depends(get_db)
):
    """
    获取指定标的的历史价格数据
    
    - **symbol**: 标的代码
    - **investment_type**: 投资类型
    - **start_date**: 开始日期（可选，格式：YYYYMMDD）
    - **end_date**: 结束日期（可选，格式：YYYYMMDD）
    - **adjust**: 复权类型（仅股票有效，默认前复权）
    
    注意：
    - 股票支持复权参数
    - 基金返回净值走势数据
    - 贵金属历史数据功能待完善
    """
    historical_data = []
    
    if investment_type == InvestmentType.STOCK:
        df = PriceService.get_stock_history(symbol, start_date, end_date, adjust)
        if df is None or df.empty:
            raise HTTPException(
                status_code=404,
                detail=f"无法获取股票 {symbol} 的历史价格数据"
            )
        
        # 转换 DataFrame 为响应格式
        for _, row in df.iterrows():
            # 解析日期，支持多种格式
            date_str = str(row.get("日期", ""))
            try:
                if len(date_str) == 8:  # YYYYMMDD
                    price_date = datetime.strptime(date_str, "%Y%m%d")
                elif len(date_str) == 10:  # YYYY-MM-DD
                    price_date = datetime.strptime(date_str, "%Y-%m-%d")
                else:
                    price_date = datetime.now()
            except:
                price_date = datetime.now()
            
            historical_data.append(
                HistoricalPriceData(
                    date=price_date,
                    price=float(row.get("收盘", row.get("净值", 0))),
                    volume=float(row.get("成交量", 0)) if "成交量" in row and pd.notna(row.get("成交量")) else None,
                    open=float(row.get("开盘", 0)) if "开盘" in row and pd.notna(row.get("开盘")) else None,
                    high=float(row.get("最高", 0)) if "最高" in row and pd.notna(row.get("最高")) else None,
                    low=float(row.get("最低", 0)) if "最低" in row and pd.notna(row.get("最低")) else None,
                    close=float(row.get("收盘", 0)) if "收盘" in row and pd.notna(row.get("收盘")) else None,
                )
            )
    
    elif investment_type == InvestmentType.FUND:
        df = PriceService.get_fund_history(symbol)
        if df is None or df.empty:
            raise HTTPException(
                status_code=404,
                detail=f"无法获取基金 {symbol} 的历史净值数据"
            )
        
        # 转换基金净值数据
        for _, row in df.iterrows():
            # 尝试多个可能的日期字段名
            date_str = str(row.get("净值日期", row.get("日期", "")))
            try:
                if len(date_str) == 8:  # YYYYMMDD
                    price_date = datetime.strptime(date_str, "%Y%m%d")
                elif len(date_str) == 10:  # YYYY-MM-DD
                    price_date = datetime.strptime(date_str, "%Y-%m-%d")
                else:
                    price_date = datetime.now()
            except:
                price_date = datetime.now()
            
            # 尝试多个可能的净值字段名
            nav_value = row.get("净值", row.get("单位净值", row.get("累计净值", 0)))
            if pd.isna(nav_value):
                nav_value = 0
            
            historical_data.append(
                HistoricalPriceData(
                    date=price_date,
                    price=float(nav_value),
                )
            )
    
    elif investment_type == InvestmentType.PRECIOUS_METAL:
        df = PriceService.get_precious_metal_history(symbol, start_date, end_date)
        if df is None or df.empty:
            raise HTTPException(
                status_code=501,
                detail=f"贵金属 {symbol} 的历史价格数据功能暂未实现"
            )
        # 如果未来实现了，可以在这里处理
    
    else:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的投资类型: {investment_type.value}"
        )
    
    return HistoricalPriceResponse(
        symbol=symbol,
        investment_type=investment_type,
        data=historical_data
    )


@router.post("/batch", response_model=BatchPriceResponse)
def get_batch_prices(
    request: BatchPriceRequest,
    db: Session = Depends(get_db)
):
    """
    批量获取多个标的的当前价格
    
    请求体示例：
    ```json
    {
        "symbols": ["600519", "000001", "黄金"],
        "investment_type": "stock"
    }
    ```
    
    注意：所有标的必须是同一投资类型
    """
    prices = []
    failed = []
    
    for symbol in request.symbols:
        try:
            price = PriceService.get_price_with_cache(db, symbol, request.investment_type)
            if price is not None:
                prices.append(
                    PriceData(
                        symbol=symbol,
                        price=price,
                        date=datetime.now()
                    )
                )
            else:
                failed.append(symbol)
        except Exception as e:
            failed.append(symbol)
    
    return BatchPriceResponse(
        prices=prices,
        failed=failed
    )

