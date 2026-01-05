"""投资记录相关的API路由"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.database import get_db
from app.models import InvestmentRecord, InvestmentType
from app.schemas import (
    InvestmentRecordCreate,
    InvestmentRecordUpdate,
    InvestmentRecordResponse,
    PositionSummary,
    PortfolioSummary,
)
from app.services.price_service import PriceService

router = APIRouter(prefix="/api/investments", tags=["investments"])


@router.post("/", response_model=InvestmentRecordResponse, status_code=201)
def create_investment_record(
    record: InvestmentRecordCreate,
    db: Session = Depends(get_db)
):
    """创建投资记录"""
    db_record = InvestmentRecord(**record.model_dump())
    db.add(db_record)
    db.commit()
    db.refresh(db_record)
    return db_record


@router.get("/", response_model=List[InvestmentRecordResponse])
def get_investment_records(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    symbol: Optional[str] = None,
    investment_type: Optional[InvestmentType] = None,
    db: Session = Depends(get_db)
):
    """获取投资记录列表"""
    query = db.query(InvestmentRecord)
    
    if symbol:
        query = query.filter(InvestmentRecord.symbol == symbol)
    if investment_type:
        query = query.filter(InvestmentRecord.investment_type == investment_type)
    
    records = query.order_by(InvestmentRecord.transaction_date.desc()).offset(skip).limit(limit).all()
    return records


@router.get("/{record_id}", response_model=InvestmentRecordResponse)
def get_investment_record(record_id: int, db: Session = Depends(get_db)):
    """获取单个投资记录"""
    record = db.query(InvestmentRecord).filter(InvestmentRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="投资记录不存在")
    return record


@router.put("/{record_id}", response_model=InvestmentRecordResponse)
def update_investment_record(
    record_id: int,
    record_update: InvestmentRecordUpdate,
    db: Session = Depends(get_db)
):
    """更新投资记录"""
    record = db.query(InvestmentRecord).filter(InvestmentRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="投资记录不存在")
    
    update_data = record_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(record, field, value)
    
    db.commit()
    db.refresh(record)
    return record


@router.delete("/{record_id}", status_code=204)
def delete_investment_record(record_id: int, db: Session = Depends(get_db)):
    """删除投资记录"""
    record = db.query(InvestmentRecord).filter(InvestmentRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="投资记录不存在")
    
    db.delete(record)
    db.commit()
    return None


@router.get("/positions/summary", response_model=List[PositionSummary])
def get_positions_summary(db: Session = Depends(get_db)):
    """获取持仓摘要"""
    # 获取所有投资记录
    records = db.query(InvestmentRecord).all()
    
    # 按symbol分组计算持仓
    positions = {}
    for record in records:
        if record.symbol not in positions:
            positions[record.symbol] = {
                "symbol": record.symbol,
                "name": record.name,
                "investment_type": record.investment_type,
                "total_quantity": 0.0,
                "total_cost": 0.0,
            }
        
        pos = positions[record.symbol]
        if record.transaction_type.value == "buy":
            pos["total_quantity"] += record.quantity
            pos["total_cost"] += record.amount + record.fee
        elif record.transaction_type.value == "sell":
            pos["total_quantity"] -= record.quantity
            # 卖出时，按平均成本计算减少的成本
            if pos["total_quantity"] > 0:
                avg_cost = pos["total_cost"] / (pos["total_quantity"] + record.quantity)
                pos["total_cost"] = pos["total_quantity"] * avg_cost
            else:
                pos["total_cost"] = 0.0
    
    # 过滤掉持仓为0的标的
    positions = {k: v for k, v in positions.items() if v["total_quantity"] > 0}
    
    # 计算平均成本和获取当前价格
    result = []
    for symbol, pos in positions.items():
        avg_cost = pos["total_cost"] / pos["total_quantity"] if pos["total_quantity"] > 0 else 0
        
        # 获取当前价格
        current_price = PriceService.get_price_with_cache(
            db, symbol, pos["investment_type"]
        )
        
        current_value = current_price * pos["total_quantity"] if current_price else None
        profit_loss = (current_value - pos["total_cost"]) if current_value else None
        profit_loss_rate = (
            (profit_loss / pos["total_cost"] * 100) if profit_loss and pos["total_cost"] > 0 else None
        )
        
        result.append(PositionSummary(
            symbol=pos["symbol"],
            name=pos["name"],
            investment_type=pos["investment_type"],
            total_quantity=pos["total_quantity"],
            average_cost=avg_cost,
            total_cost=pos["total_cost"],
            current_price=current_price,
            current_value=current_value,
            profit_loss=profit_loss,
            profit_loss_rate=profit_loss_rate,
        ))
    
    return result


@router.get("/portfolio/summary", response_model=PortfolioSummary)
def get_portfolio_summary(db: Session = Depends(get_db)):
    """获取投资组合摘要"""
    positions = get_positions_summary(db)
    
    total_cost = sum(p.total_cost for p in positions)
    total_value = sum(p.current_value for p in positions if p.current_value)
    total_profit_loss = total_value - total_cost if total_value else None
    total_profit_loss_rate = (
        (total_profit_loss / total_cost * 100) if total_profit_loss and total_cost > 0 else None
    )
    
    return PortfolioSummary(
        total_cost=total_cost,
        total_value=total_value if total_value else 0.0,
        total_profit_loss=total_profit_loss if total_profit_loss else 0.0,
        total_profit_loss_rate=total_profit_loss_rate if total_profit_loss_rate else 0.0,
        positions=positions,
    )

