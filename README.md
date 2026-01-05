# 投资记录管理系统

一个基于 Python FastAPI + Streamlit 的投资记录管理 Web 应用。

## 功能特性

- 📝 **投资记录管理**：记录买入/卖出交易，支持增删改查
- 📊 **持仓情况展示**：实时查看持仓明细和市值分布
- 💰 **投资组合摘要**：查看整体盈亏情况和各标的表现
- 📈 **价值变化图表**：可视化每个标的的持仓和成本变化趋势
- 🔄 **实时价格获取**：通过 akshare 获取股票、基金等实时价格

## 技术栈

- **后端**：FastAPI + SQLAlchemy + SQLite
- **前端**：Streamlit + Plotly
- **数据源**：akshare（股票、基金价格）

## 安装和运行

### 1. 安装依赖

使用 Poetry 安装依赖：

```bash
poetry install
```

### 2. 运行应用

#### 方式一：使用启动脚本（推荐）

```bash
./run.sh
```

这个脚本会自动启动后端和前端服务。

#### 方式二：手动启动

**启动后端：**

```bash
poetry run uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**启动前端（新开一个终端）：**

```bash
poetry run streamlit run frontend.py --server.port 8501
```

### 3. 访问应用

- **前端界面**：http://localhost:8501
- **API 文档**：http://localhost:8000/docs
- **API 健康检查**：http://localhost:8000/health

## 使用说明

### 添加投资记录

1. 在"投资记录"页面，点击"➕ 添加新投资记录"
2. 填写标的代码、名称、投资类型、交易类型等信息
3. 点击"提交"保存记录

### 查看持仓情况

在"持仓情况"页面可以查看：
- 所有持仓标的的详细信息
- 持仓市值分布饼图
- 各标的的盈亏情况

### 查看投资组合

在"投资组合"页面可以查看：
- 总成本、总市值、总盈亏等关键指标
- 各标的的盈亏柱状图
- 各标的的盈亏率对比

### 查看价值变化

在"价值变化图表"页面：
1. 选择要查看的标的
2. 查看该标的的持仓数量变化趋势
3. 查看累计成本变化趋势

## API 端点

### 投资记录

- `GET /api/investments/` - 获取投资记录列表
- `POST /api/investments/` - 创建投资记录
- `GET /api/investments/{record_id}` - 获取单个投资记录
- `PUT /api/investments/{record_id}` - 更新投资记录
- `DELETE /api/investments/{record_id}` - 删除投资记录

### 持仓和组合

- `GET /api/investments/positions/summary` - 获取持仓摘要
- `GET /api/investments/portfolio/summary` - 获取投资组合摘要

### 价格

- `GET /api/prices/{symbol}?investment_type={type}` - 获取标的当前价格

## 数据库

应用使用 SQLite 数据库，数据库文件为 `investment.db`，会在首次运行时自动创建。

## 注意事项

1. 股票代码格式：可以使用 6 位数字（如 `000001`）或带市场前缀（如 `sz000001`）
2. 价格缓存：价格数据会缓存 1 小时，减少 API 调用
3. 首次获取价格可能需要一些时间，请耐心等待

## 开发

项目结构：

```
cracker/
├── app/
│   ├── database.py          # 数据库配置
│   ├── models.py            # 数据模型
│   ├── schemas.py           # API schemas
│   ├── routers/             # API 路由
│   └── services/            # 业务逻辑服务
├── main.py                  # FastAPI 主应用
├── frontend.py              # Streamlit 前端
└── pyproject.toml           # 项目配置

