"""价格相关的API路由"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.models import InvestmentType
from app.schemas import PriceData
from app.services.price_service import PriceService

router = APIRouter(prefix="/api/prices", tags=["prices"])


@router.get("/{symbol}", response_model=PriceData)
def get_price(
    symbol: str,
    investment_type: InvestmentType,
    db: Session = Depends(get_db)
):
    """获取指定标的的当前价格"""
    price = PriceService.get_price_with_cache(db, symbol, investment_type)
    
    if price is None:
        raise HTTPException(
            status_code=404,
            detail=f"无法获取 {symbol} 的价格，请检查代码是否正确"
        )
    
    from datetime import datetime
    return PriceData(
        symbol=symbol,
        price=price,
        date=datetime.now()
    )

