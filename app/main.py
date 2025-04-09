from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routers import all_routers

# from app.db.session import engine # 如果需要创建表
# from app.models.story_element import Base # 如果需要创建表

# --- 如果需要自动创建数据库表 (仅适用于开发初期) ---
# def create_tables():
#     Base.metadata.create_all(bind=engine)
# create_tables()
# --------------------------------------------------

app = FastAPI(title="Novel Writer AI Backend")

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_ORIGIN], # 允许来自前端的请求
    allow_credentials=True,
    allow_methods=["*"], # 允许所有方法
    allow_headers=["*"], # 允许所有头部
)

@app.get("/")
def read_root():
    return {"message": "Welcome to the Novel Writer AI Backend!"}

# Include routers
for router in all_routers:
    app.include_router(router, prefix="/api", tags=[router.prefix.strip('/').split('/')[0] or 'default']) # Basic tagging by first path element
