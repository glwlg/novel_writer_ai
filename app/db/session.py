# backend/app/db/session.py

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# --- PGVector 相关 ---
# 通常在模型定义或首次连接时确保扩展已启用
# 更好的方式是在数据库级别手动创建扩展
def check_pgvector_extension():
     with engine.connect() as connection:
        try:
            # 尝试查询向量相关的函数确认扩展是否可用
            connection.execute("SELECT embedding::vector FROM (SELECT array[1,2,3] AS embedding) AS t LIMIT 1;")
            print("PGVector extension seems enabled.")
        except Exception as e:
            print(f"PGVector extension check failed: {e}")
            print("Please ensure the PGVector extension is created in your database: CREATE EXTENSION vector;")
# check_pgvector_extension() # 可以在启动时检查，但手动创建更可靠

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()