# backend/app/schemas/character.py
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List
from datetime import datetime

# --- Character Schemas ---
class CharacterBase(BaseModel):
    name: str
    description: Optional[str] = None
    backstory: Optional[str] = None
    goals: Optional[str] = None
    arc_summary: Optional[str] = None
    current_status: Optional[str] = None

class CharacterCreate(CharacterBase):
    project_id: int # 创建时必须指定项目

class CharacterUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    backstory: Optional[str] = None
    goals: Optional[str] = None
    arc_summary: Optional[str] = None
    current_status: Optional[str] = None
    # project_id 通常不允许修改，或者需要特殊逻辑处理

class CharacterRead(CharacterBase):
    id: int
    project_id: int
    # embedding 字段通常不在API中返回给前端
    # embedding: Optional[List[float]] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

# 可选：用于在 ProjectRead 中嵌套显示的简化版
class CharacterReadMinimal(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)