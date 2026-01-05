"""Streamlit前端应用"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date
from typing import Optional

from app.models import InvestmentType, TransactionType
from app.schemas import InvestmentRecordCreate, InvestmentRecordUpdate
from app.services.investment_service import (
    create_investment_record_service,
    get_investment_records_service,
    get_investment_record_service,
    update_investment_record_service,
    delete_investment_record_service,
    get_positions_summary_service,
    get_portfolio_summary_service,
)

# 配置页面
st.set_page_config(
    page_title="投资记录管理系统",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 初始化session state
if "records" not in st.session_state:
    st.session_state.records = []
if "positions" not in st.session_state:
    st.session_state.positions = []
if "portfolio" not in st.session_state:
    st.session_state.portfolio = None


def fetch_investment_records(symbol: Optional[str] = None, investment_type: Optional[InvestmentType] = None):
    """获取投资记录"""
    try:
        records = get_investment_records_service(symbol=symbol, investment_type=investment_type)
        return [r.model_dump() for r in records]
    except Exception as e:
        st.error(f"获取投资记录失败: {str(e)}")
        return []


def fetch_positions():
    """获取持仓摘要"""
    try:
        positions = get_positions_summary_service()
        return [p.model_dump() for p in positions]
    except Exception as e:
        st.error(f"获取持仓摘要失败: {str(e)}")
        return []


def fetch_portfolio():
    """获取投资组合摘要"""
    try:
        portfolio = get_portfolio_summary_service()
        return portfolio.model_dump()
    except Exception as e:
        st.error(f"获取投资组合摘要失败: {str(e)}")
        return None


def create_investment_record(record_data: dict):
    """创建投资记录"""
    try:
        record = InvestmentRecordCreate(**record_data)
        result = create_investment_record_service(record)
        return result.model_dump()
    except Exception as e:
        st.error(f"创建投资记录失败: {str(e)}")
        return None


def update_investment_record(record_id: int, record_data: dict):
    """更新投资记录"""
    try:
        record_update = InvestmentRecordUpdate(**record_data)
        result = update_investment_record_service(record_id, record_update)
        if result:
            return result.model_dump()
        return None
    except Exception as e:
        st.error(f"更新投资记录失败: {str(e)}")
        return None


def delete_investment_record(record_id: int):
    """删除投资记录"""
    try:
        return delete_investment_record_service(record_id)
    except Exception as e:
        st.error(f"删除投资记录失败: {str(e)}")
        return False


def format_currency(value: float) -> str:
    """格式化货币显示"""
    if value is None:
        return "N/A"
    return f"¥{value:,.2f}"


def format_percentage(value: Optional[float]) -> str:
    """格式化百分比显示"""
    if value is None:
        return "N/A"
    return f"{value:.2f}%"


def main():
    st.title("📈 投资记录管理系统")
    
    # 侧边栏
    with st.sidebar:
        st.header("导航")
        page = st.radio(
            "选择页面",
            ["投资记录", "持仓情况", "投资组合", "价值变化"],
            index=0
        )
        
        st.divider()
        if st.button("🔄 刷新数据", use_container_width=True):
            st.session_state.records = fetch_investment_records()
            st.session_state.positions = fetch_positions()
            st.session_state.portfolio = fetch_portfolio()
            st.rerun()
    
    # 根据选择的页面显示内容
    if page == "投资记录":
        show_investment_records()
    elif page == "持仓情况":
        show_positions()
    elif page == "投资组合":
        show_portfolio()
    elif page == "价值变化":
        show_value_charts()


def show_investment_records():
    """显示投资记录管理页面"""
    st.header("投资记录管理")
    
    # 刷新数据
    if not st.session_state.records:
        st.session_state.records = fetch_investment_records()
    
    # 添加新记录
    with st.expander("➕ 添加新投资记录", expanded=False):
        with st.form("add_record_form"):
            col1, col2 = st.columns(2)
            with col1:
                symbol = st.text_input("标的代码*", placeholder="如: 000001")
                name = st.text_input("标的名称*", placeholder="如: 平安银行")
                investment_type = st.selectbox(
                    "投资类型*",
                    [InvestmentType.STOCK, InvestmentType.FUND, InvestmentType.BOND, InvestmentType.OTHER],
                    format_func=lambda x: {"stock": "股票", "fund": "基金", "bond": "债券", "other": "其他"}.get(x, x)
                )
                transaction_type = st.selectbox(
                    "交易类型*",
                    [TransactionType.BUY, TransactionType.SELL],
                    format_func=lambda x: {"buy": "买入", "sell": "卖出"}.get(x, x)
                )
            
            with col2:
                quantity = st.number_input("交易数量*", min_value=0.01, step=0.01, format="%.2f")
                price = st.number_input("交易价格*", min_value=0.01, step=0.01, format="%.2f")
                amount = st.number_input("交易金额*", min_value=0.01, step=0.01, format="%.2f")
                fee = st.number_input("手续费", min_value=0.0, step=0.01, format="%.2f", value=0.0)
            
            transaction_date = st.date_input("交易日期*", value=date.today())
            notes = st.text_area("备注")
            
            submitted = st.form_submit_button("提交", use_container_width=True)
            
            if submitted:
                record_data = {
                    "symbol": symbol,
                    "name": name,
                    "investment_type": investment_type.value,
                    "transaction_type": transaction_type.value,
                    "quantity": quantity,
                    "price": price,
                    "amount": amount,
                    "fee": fee,
                    "transaction_date": datetime.combine(transaction_date, datetime.min.time()).isoformat(),
                    "notes": notes
                }
                result = create_investment_record(record_data)
                if result:
                    st.success("投资记录创建成功！")
                    st.session_state.records = fetch_investment_records()
                    st.rerun()
    
    # 显示记录列表
    st.subheader("投资记录列表")
    
    # 筛选选项
    col1, col2 = st.columns(2)
    with col1:
        filter_symbol = st.text_input("按代码筛选", key="filter_symbol")
    with col2:
        filter_type = st.selectbox(
            "按类型筛选",
            ["全部", InvestmentType.STOCK, InvestmentType.FUND, InvestmentType.BOND, InvestmentType.OTHER],
            key="filter_type",
            format_func=lambda x: {"全部": "全部", "stock": "股票", "fund": "基金", "bond": "债券", "other": "其他"}.get(x, x)
        )
    
    # 筛选记录
    filtered_records = st.session_state.records
    if filter_symbol:
        filtered_records = [r for r in filtered_records if filter_symbol.lower() in r["symbol"].lower()]
    if filter_type != "全部":
        filter_type_value = filter_type.value if hasattr(filter_type, 'value') else filter_type
        filtered_records = [r for r in filtered_records if r["investment_type"] == filter_type_value]
    
    if filtered_records:
        # 转换为DataFrame显示
        df = pd.DataFrame(filtered_records)
        # 格式化日期
        df["transaction_date"] = pd.to_datetime(df["transaction_date"]).dt.strftime("%Y-%m-%d")
        df["created_at"] = pd.to_datetime(df["created_at"]).dt.strftime("%Y-%m-%d %H:%M")
        
        # 选择要显示的列
        display_columns = [
            "id", "symbol", "name", "investment_type", "transaction_type",
            "quantity", "price", "amount", "fee", "transaction_date", "notes"
        ]
        
        st.dataframe(
            df[display_columns],
            use_container_width=True,
            hide_index=True
        )
        
        # 编辑和删除功能
        st.subheader("编辑/删除记录")
        record_ids = [str(r["id"]) for r in filtered_records]
        selected_id = st.selectbox("选择要操作的记录ID", record_ids)
        
        if selected_id:
            record_id = int(selected_id)
            selected_record = next(r for r in filtered_records if r["id"] == record_id)
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🗑️ 删除记录", use_container_width=True, type="primary"):
                    if delete_investment_record(record_id):
                        st.success("记录删除成功！")
                        st.session_state.records = fetch_investment_records()
                        st.rerun()
            
            with col2:
                if st.button("✏️ 编辑记录", use_container_width=True):
                    st.session_state.edit_record_id = record_id
                    st.session_state.edit_record = selected_record
                    st.rerun()
            
            # 编辑表单
            if "edit_record_id" in st.session_state and st.session_state.edit_record_id == record_id:
                with st.expander("编辑投资记录", expanded=True):
                    with st.form("edit_record_form"):
                        col1, col2 = st.columns(2)
                        with col1:
                            edit_symbol = st.text_input("标的代码", value=selected_record["symbol"])
                            edit_name = st.text_input("标的名称", value=selected_record["name"])
                            investment_types = [InvestmentType.STOCK, InvestmentType.FUND, InvestmentType.BOND, InvestmentType.OTHER]
                            investment_type_values = [t.value for t in investment_types]
                            investment_type_index = investment_type_values.index(selected_record["investment_type"]) if selected_record["investment_type"] in investment_type_values else 0
                            edit_investment_type = st.selectbox(
                                "投资类型",
                                investment_types,
                                index=investment_type_index,
                                format_func=lambda x: {"stock": "股票", "fund": "基金", "bond": "债券", "other": "其他"}.get(x.value if hasattr(x, 'value') else x, x)
                            )
                            transaction_types = [TransactionType.BUY, TransactionType.SELL]
                            transaction_type_values = [t.value for t in transaction_types]
                            transaction_type_index = transaction_type_values.index(selected_record["transaction_type"]) if selected_record["transaction_type"] in transaction_type_values else 0
                            edit_transaction_type = st.selectbox(
                                "交易类型",
                                transaction_types,
                                index=transaction_type_index,
                                format_func=lambda x: {"buy": "买入", "sell": "卖出"}.get(x.value if hasattr(x, 'value') else x, x)
                            )
                        
                        with col2:
                            edit_quantity = st.number_input("交易数量", min_value=0.01, step=0.01, format="%.2f", value=selected_record["quantity"])
                            edit_price = st.number_input("交易价格", min_value=0.01, step=0.01, format="%.2f", value=selected_record["price"])
                            edit_amount = st.number_input("交易金额", min_value=0.01, step=0.01, format="%.2f", value=selected_record["amount"])
                            edit_fee = st.number_input("手续费", min_value=0.0, step=0.01, format="%.2f", value=selected_record["fee"])
                        
                        edit_transaction_date = st.date_input(
                            "交易日期",
                            value=pd.to_datetime(selected_record["transaction_date"]).date()
                        )
                        edit_notes = st.text_area("备注", value=selected_record.get("notes", ""))
                        
                        submitted = st.form_submit_button("更新", use_container_width=True)
                        
                        if submitted:
                            update_data = {
                                "symbol": edit_symbol,
                                "name": edit_name,
                                "investment_type": edit_investment_type.value,
                                "transaction_type": edit_transaction_type.value,
                                "quantity": edit_quantity,
                                "price": edit_price,
                                "amount": edit_amount,
                                "fee": edit_fee,
                                "transaction_date": datetime.combine(edit_transaction_date, datetime.min.time()).isoformat(),
                                "notes": edit_notes
                            }
                            result = update_investment_record(record_id, update_data)
                            if result:
                                st.success("记录更新成功！")
                                del st.session_state.edit_record_id
                                del st.session_state.edit_record
                                st.session_state.records = fetch_investment_records()
                                st.rerun()
    else:
        st.info("暂无投资记录")


def show_positions():
    """显示持仓情况页面"""
    st.header("持仓情况")
    
    # 刷新数据
    if not st.session_state.positions:
        st.session_state.positions = fetch_positions()
    
    positions = st.session_state.positions
    
    if positions:
        # 转换为DataFrame
        df = pd.DataFrame(positions)
        
        # 显示统计卡片
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("持仓标的数", len(positions))
        with col2:
            total_cost = sum(p["total_cost"] for p in positions)
            st.metric("总成本", format_currency(total_cost))
        with col3:
            total_value = sum(p["current_value"] for p in positions if p["current_value"])
            st.metric("总市值", format_currency(total_value) if total_value else "N/A")
        with col4:
            total_profit = total_value - total_cost if total_value else None
            st.metric("总盈亏", format_currency(total_profit) if total_profit else "N/A")
        
        # 持仓表格
        st.subheader("持仓明细")
        display_df = df.copy()
        display_df["average_cost"] = display_df["average_cost"].apply(format_currency)
        display_df["total_cost"] = display_df["total_cost"].apply(format_currency)
        display_df["current_price"] = display_df["current_price"].apply(lambda x: format_currency(x) if x else "N/A")
        display_df["current_value"] = display_df["current_value"].apply(lambda x: format_currency(x) if x else "N/A")
        display_df["profit_loss"] = display_df["profit_loss"].apply(lambda x: format_currency(x) if x else "N/A")
        display_df["profit_loss_rate"] = display_df["profit_loss_rate"].apply(format_percentage)
        
        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True
        )
        
        # 持仓分布饼图
        if total_value:
            st.subheader("持仓分布（按市值）")
            fig = px.pie(
                df,
                values="current_value",
                names="name",
                title="持仓市值分布"
            )
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("暂无持仓")


def show_portfolio():
    """显示投资组合摘要页面"""
    st.header("投资组合摘要")
    
    # 刷新数据
    if not st.session_state.portfolio:
        st.session_state.portfolio = fetch_portfolio()
    
    portfolio = st.session_state.portfolio
    
    if portfolio:
        # 主要指标
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("总成本", format_currency(portfolio["total_cost"]))
        with col2:
            st.metric("总市值", format_currency(portfolio["total_value"]))
        with col3:
            profit_loss = portfolio["total_profit_loss"]
            profit_color = "normal" if profit_loss >= 0 else "inverse"
            st.metric("总盈亏", format_currency(profit_loss), delta=format_percentage(portfolio["total_profit_loss_rate"]))
        with col4:
            st.metric("持仓标的数", len(portfolio["positions"]))
        
        # 盈亏分布图
        if portfolio["positions"]:
            st.subheader("各标的盈亏情况")
            positions_df = pd.DataFrame(portfolio["positions"])
            
            fig = go.Figure()
            colors = ["green" if p >= 0 else "red" for p in positions_df["profit_loss"]]
            fig.add_trace(go.Bar(
                x=positions_df["name"],
                y=positions_df["profit_loss"],
                marker_color=colors,
                text=[format_currency(p) for p in positions_df["profit_loss"]],
                textposition="outside"
            ))
            fig.update_layout(
                title="各标的盈亏情况",
                xaxis_title="标的名称",
                yaxis_title="盈亏金额（元）",
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # 盈亏率分布
            st.subheader("各标的盈亏率")
            fig2 = go.Figure()
            colors2 = ["green" if p >= 0 else "red" for p in positions_df["profit_loss_rate"]]
            fig2.add_trace(go.Bar(
                x=positions_df["name"],
                y=positions_df["profit_loss_rate"],
                marker_color=colors2,
                text=[format_percentage(p) for p in positions_df["profit_loss_rate"]],
                textposition="outside"
            ))
            fig2.update_layout(
                title="各标的盈亏率",
                xaxis_title="标的名称",
                yaxis_title="盈亏率（%）",
                height=400
            )
            st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("暂无投资组合数据")


def show_value_charts():
    """显示价值变化图表页面"""
    st.header("价值变化图表")
    
    # 刷新数据
    if not st.session_state.records:
        st.session_state.records = fetch_investment_records()
    
    records = st.session_state.records
    
    if records:
        # 选择要查看的标的
        symbols = list(set(r["symbol"] for r in records))
        selected_symbol = st.selectbox("选择标的", symbols)
        
        if selected_symbol:
            # 筛选该标的的记录
            symbol_records = [r for r in records if r["symbol"] == selected_symbol]
            symbol_records.sort(key=lambda x: x["transaction_date"])
            
            # 计算累计持仓和成本
            cumulative_quantity = 0
            cumulative_cost = 0
            timeline_data = []
            
            for record in symbol_records:
                if record["transaction_type"] == "buy":
                    cumulative_quantity += record["quantity"]
                    cumulative_cost += record["amount"] + record["fee"]
                else:  # sell
                    cumulative_quantity -= record["quantity"]
                    # 简化处理：按平均成本减少
                    if cumulative_quantity > 0:
                        avg_cost = cumulative_cost / (cumulative_quantity + record["quantity"])
                        cumulative_cost = cumulative_quantity * avg_cost
                    else:
                        cumulative_cost = 0
                
                timeline_data.append({
                    "date": pd.to_datetime(record["transaction_date"]),
                    "quantity": cumulative_quantity,
                    "cost": cumulative_cost,
                    "avg_cost": cumulative_cost / cumulative_quantity if cumulative_quantity > 0 else 0
                })
            
            if timeline_data:
                df_timeline = pd.DataFrame(timeline_data)
                
                # 持仓数量变化图
                st.subheader(f"{selected_symbol} 持仓数量变化")
                fig1 = px.line(
                    df_timeline,
                    x="date",
                    y="quantity",
                    title="持仓数量变化",
                    markers=True
                )
                fig1.update_layout(
                    xaxis_title="日期",
                    yaxis_title="持仓数量",
                    height=400
                )
                st.plotly_chart(fig1, use_container_width=True)
                
                # 成本变化图
                st.subheader(f"{selected_symbol} 累计成本变化")
                fig2 = px.line(
                    df_timeline,
                    x="date",
                    y="cost",
                    title="累计成本变化",
                    markers=True
                )
                fig2.update_layout(
                    xaxis_title="日期",
                    yaxis_title="累计成本（元）",
                    height=400
                )
                st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("暂无投资记录，无法显示图表")


if __name__ == "__main__":
    main()

