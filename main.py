"""FastAPI主应用"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.database import init_db
from app.routers import investments, prices

# 创建FastAPI应用
app = FastAPI(
    title="投资记录管理系统",
    description="一个简单的投资记录管理Web应用",
    version="0.1.0"
)

# 配置CORS，允许前端跨域访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该设置具体的域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(investments.router)
app.include_router(prices.router)


@app.on_event("startup")
async def startup_event():
    """应用启动时初始化数据库"""
    logger.info("初始化数据库...")
    init_db()
    logger.info("数据库初始化完成")


@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "投资记录管理系统API",
        "docs": "/docs",
        "version": "0.1.0"
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy"}

