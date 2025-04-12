# backend/app/schemas/scenes.py

from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime
# 导入你在 models.structure 中定义的 SceneStatus Enum
# 假设它在 app.models.structure 文件中
from app.models.structure import SceneStatus

# --- Scene Base Schema ---
# 包含所有 Scene 模型共有的、且可能在创建或读取时用到的字段
# 可以不直接使用，作为 Create 和 Read 的基类
class SceneBase(BaseModel):
    title: Optional[str] = None
    goal: Optional[str] = None # 虽然创建时可能必需，但基类中设为 Optional 增加灵活性
    summary: Optional[str] = None
    generated_content: Optional[str] = None
    order_in_chapter: int = 0
    status: SceneStatus = SceneStatus.PLANNED

# --- Scene Create Schema ---
# 用于 API 创建新 Scene 时，校验请求体的数据
# 只包含创建时需要用户提供（或允许提供）的字段
class SceneCreate(SceneBase):
    project_id: int          # 创建时必须指定关联的项目
    chapter_id: Optional[int] = None # 可以先不指定章节，或者在创建时指定
    goal: str                # 覆盖基类，设为必需，因为场景目标通常是创建时的核心输入
    order_in_chapter: Optional[int] = 0 # 允许用户指定顺序，默认为 0

    # 注意：像 id, created_at, updated_at, embeddings 等字段不应在这里
    # 因为它们要么是数据库自动生成，要么是内部处理逻辑

# --- Scene Update Schema --- (可选，但通常需要)
# 用于更新 Scene 记录，所有字段都是可选的
class SceneUpdate(BaseModel):
    title: Optional[str] = None
    goal: Optional[str] = None
    summary: Optional[str] = None
    # summary_embedding: Optional[List[float]] = None
    generated_content: Optional[str] = None
    order_in_chapter: Optional[int] = None
    status: Optional[SceneStatus] = None
    chapter_id: Optional[int] = None # 允许移动章节

# --- Scene Update Schema --- (可选，但通常需要)
# 用于更新 Scene 记录，所有字段都是可选的
class SceneUpdateGenerated(BaseModel):
    generated_content: str
    summary: Optional[str] = None
    summary_embedding: Optional[List[float]] = None
    status: Optional[SceneStatus] = None

# --- Scene Read Schema ---
# 用于 API 返回 Scene 数据给前端
# 包含希望返回给客户端的所有字段
class SceneRead(SceneBase):
    id: int                 # 数据库生成的 ID 是必须返回的
    project_id: int
    chapter_id: Optional[int]
    created_at: datetime
    updated_at: Optional[datetime] = None # 首次创建时可能为 None

    # Pydantic V2 使用 model_config
    model_config = ConfigDict(
        from_attributes=True  # 允许 Pydantic 从 ORM 对象的属性读取数据
    )

    # Pydantic V1 使用 Config 子类 (如果你的 Pydantic 版本较旧)
    # class Config:
    #     orm_mode = True

# --- (可选) 用于嵌套显示的简化 Schema ---
# 在返回 Chapter 或 Project 时，可能只需要 Scene 的部分信息
class SceneReadMinimal(BaseModel):
    id: int
    title: Optional[str]
    chapter_id: int
    order_in_chapter: int
    status: SceneStatus

    model_config = ConfigDict(from_attributes=True)
    # class Config:
    #     orm_mode = True