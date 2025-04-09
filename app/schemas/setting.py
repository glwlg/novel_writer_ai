# backend/app/schemas/setting.py
from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime

# --- SettingElement Schemas ---
class SettingElementBase(BaseModel):
    name: str
    element_type: str # e.g., 'Location', 'Item', 'Concept'
    description: Optional[str] = None

class SettingElementCreate(SettingElementBase):
    project_id: int # 创建时必须指定项目

class SettingElementUpdate(BaseModel):
    name: Optional[str] = None
    element_type: Optional[str] = None
    description: Optional[str] = None
    # project_id 通常不允许修改

class SettingElementRead(SettingElementBase):
    id: int
    project_id: int
    # embedding: Optional[List[float]] = None # 通常不返回
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

# 可选：用于在 ProjectRead 中嵌套显示的简化版
class SettingElementReadMinimal(BaseModel):
    id: int
    name: str
    element_type: str

    model_config = ConfigDict(from_attributes=True)