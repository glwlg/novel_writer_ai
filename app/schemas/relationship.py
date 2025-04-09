# backend/app/schemas/relationship.py
from pydantic import BaseModel, ConfigDict, validator
from typing import Optional, List
from datetime import datetime

# --- CharacterRelationship Schemas ---
class CharacterRelationshipBase(BaseModel):
    character1_id: int
    character2_id: int
    relationship_type: str # e.g., "Friend", "Enemy", "Family"
    description: Optional[str] = None

    @validator('character2_id')
    def characters_must_be_different(cls, v, values):
        if 'character1_id' in values and v == values['character1_id']:
            raise ValueError('Character1 and Character2 cannot be the same')
        return v

class CharacterRelationshipCreate(CharacterRelationshipBase):
    project_id: int # 创建时需要指定项目以校验角色归属

class CharacterRelationshipUpdate(BaseModel):
    # 通常不允许修改 character1_id, character2_id, project_id
    relationship_type: Optional[str] = None
    description: Optional[str] = None

class CharacterRelationshipRead(CharacterRelationshipBase):
    id: int
    project_id: int
    # embedding: Optional[List[float]] = None # 通常不返回
    created_at: datetime
    updated_at: Optional[datetime] = None

    # 可选: 嵌套显示关联的角色信息
    # character1: CharacterReadMinimal
    # character2: CharacterReadMinimal

    model_config = ConfigDict(from_attributes=True)

# 可以在 CharacterRead 中包含的关系简化信息
class RelationshipInfoForCharacterRead(BaseModel):
    related_character_id: int
    related_character_name: str # 需要在查询时组装
    relationship_type: str
    description: Optional[str] = None

    model_config = ConfigDict(from_attributes=True) # 如果数据源是 ORM 对象属性