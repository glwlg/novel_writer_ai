# backend/app/schemas/project.py
from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime
# 导入其他需要的 Read schemas 以便嵌套显示 (如果需要)
from .character import CharacterReadMinimal # 示例
from .setting import SettingElementReadMinimal   # 示例
from .chapter import ChapterReadMinimal   # 示例

class ProjectBase(BaseModel):
    title: str
    logline: Optional[str] = None
    global_synopsis: Optional[str] = None

class ProjectCreate(ProjectBase):
    pass # 创建时只需要 ProjectBase 中的字段

class ProjectUpdate(BaseModel):
    title: Optional[str] = None
    logline: Optional[str] = None
    global_synopsis: Optional[str] = None

class ProjectRead(ProjectBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    # 如果需要返回关联数据，可以在这里添加，并确保查询时使用了 joinedload 或 selectinload
    characters: List[CharacterReadMinimal] = []
    setting_elements: List[SettingElementReadMinimal] = []
    chapters: List[ChapterReadMinimal] = []

    model_config = ConfigDict(from_attributes=True)