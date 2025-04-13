# backend/app/schemas/volume.py
from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime

from .chapter import ChapterReadMinimal, ChapterRead


class VolumeBase(BaseModel):
    title: str
    summary: Optional[str] = None
    order: int = 0 # 提供默认值

class VolumeCreate(VolumeBase):
    project_id: int # 创建时必须指定项目
    order: Optional[int] = 0 # 允许创建时指定顺序，否则默认为0

class VolumeUpdate(BaseModel):
    title: Optional[str] = None
    summary: Optional[str] = None
    order: Optional[int] = None
    # project_id 通常不允许修改

class VolumeRead(VolumeBase):
    id: int
    project_id: int
    # embedding 不返回
    created_at: datetime
    updated_at: Optional[datetime] = None
    # 嵌套显示该卷下的章节（简化信息）
    # 注意：需要在获取数据的查询中明确加载 chapters (e.g., using options(selectinload(Volume.chapters)))
    chapters: List[ChapterRead] = []

    model_config = ConfigDict(from_attributes=True)

# 可选：用于在 ProjectRead 中嵌套显示的简化版
class VolumeReadMinimal(BaseModel):
    id: int
    title: str
    order: int

    chapters: List[ChapterReadMinimal] = []

    model_config = ConfigDict(from_attributes=True)