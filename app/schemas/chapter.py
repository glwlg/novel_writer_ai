# backend/app/schemas/chapter.py
from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime
# 导入 Scene 的简化 Schema 用于嵌套显示
from .scene import SceneReadMinimal, SceneRead


class ChapterBase(BaseModel):
    title: str
    summary: Optional[str] = None
    order: int = 0 # 提供默认值

class ChapterCreate(ChapterBase):
    project_id: int # 创建时必须指定项目
    volume_id: int # 创建时必须指定项目
    order: Optional[int] = 0 # 允许创建时指定顺序，否则默认为0

class ChapterUpdate(BaseModel):
    title: Optional[str] = None
    summary: Optional[str] = None
    order: Optional[int] = None
    content: Optional[str] = None # 完整小说内容
    # project_id 通常不允许修改

class ChapterRead(ChapterBase):
    id: int
    project_id: int
    volume_id: int
    # embedding 不返回
    created_at: datetime
    updated_at: Optional[datetime] = None
    # 嵌套显示该章节下的场景（简化信息）
    # 注意：需要在获取数据的查询中明确加载 scenes (e.g., using options(selectinload(Chapter.scenes)))
    content: Optional[str] = None # 完整小说内容
    scenes: List[SceneRead] = []

    model_config = ConfigDict(from_attributes=True)

# 可选：用于在 ProjectRead 中嵌套显示的简化版
class ChapterReadMinimal(BaseModel):
    id: int
    title: str
    order: int

    scenes: List[SceneReadMinimal] = []
    model_config = ConfigDict(from_attributes=True)