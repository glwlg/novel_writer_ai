# backend/app/services/relationship_service.py
from typing import List, Optional

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.character import CharacterRelationship
from app.schemas.relationship import CharacterRelationshipCreate, CharacterRelationshipUpdate
from app.services.llm_service import get_embedding, prepare_text_for_embedding
from .character_service import get_character  # 引入 get_character 用于校验


async def create_character_relationship(db: Session,
                                        relationship: CharacterRelationshipCreate) -> CharacterRelationship:
    """创建新的人物关系并生成 Embedding"""

    # 1. 验证 Project 存在 (虽然外键会处理，但提前校验更友好)
    #    这里省略，假设 project_id 来源于可信上下文 (如 URL 参数已验证)

    # 2. 验证两个 Character 是否存在且属于同一个 Project
    char1 = get_character(db, relationship.character1_id)
    char2 = get_character(db, relationship.character2_id)

    if not char1 or not char2:
        raise ValueError("One or both characters not found.")
    if char1.project_id != relationship.project_id or char2.project_id != relationship.project_id:
        raise ValueError("Characters must belong to the specified project.")
    if char1.id == char2.id:  # 双重检查，虽然 schema validator 做了
        raise ValueError("Cannot create a relationship with the same character.")

    # 3. 准备 Embedding
    text_for_embedding = prepare_text_for_embedding(relationship.relationship_type, relationship.description)
    embedding_vector = await get_embedding(text_for_embedding)

    # 4. 创建对象
    db_relationship = CharacterRelationship(
        **relationship.model_dump(),
        embedding=embedding_vector
    )

    # 5. 添加到数据库并处理唯一约束
    db.add(db_relationship)
    try:
        db.commit()
        db.refresh(db_relationship)
        return db_relationship
    except IntegrityError as e:
        db.rollback()
        # 检查唯一约束冲突 (character1_id, character2_id, relationship_type)
        # 注意: 实际应用中可能需要考虑 (c1, c2, type) 和 (c2, c1, type) 是否视为相同关系
        if "_character_relationship_uc" in str(e.orig):
            raise ValueError(
                f"A relationship of type '{relationship.relationship_type}' already exists between these characters (or its inverse).")
        elif "characters_fk" in str(e.orig) or "projects_fk" in str(e.orig):  # 外键错误
            raise ValueError("Invalid character or project reference.")
        else:
            raise ValueError("Failed to create character relationship due to a database constraint.")


def get_character_relationship(db: Session, relationship_id: int) -> Optional[CharacterRelationship]:
    """通过 ID 获取人物关系"""
    return db.query(CharacterRelationship).filter(CharacterRelationship.id == relationship_id).first()


def get_relationships_by_project(db: Session, project_id: int, skip: int = 0, limit: int = 100) -> List[
    CharacterRelationship]:
    """获取指定项目下的人物关系列表（分页）"""
    # 这里可以添加 .options(joinedload(CharacterRelationship.character1), joinedload(CharacterRelationship.character2))
    # 如果 Read Schema 需要嵌套角色信息
    return db.query(CharacterRelationship).filter(CharacterRelationship.project_id == project_id).offset(skip).limit(
        limit).all()


def get_relationships_for_character(db: Session, character_id: int) -> List[CharacterRelationship]:
    """获取指定角色的所有关系"""
    return db.query(CharacterRelationship).filter(
        (CharacterRelationship.character1_id == character_id) |
        (CharacterRelationship.character2_id == character_id)
    ).all()


async def update_character_relationship(db: Session, db_relationship: CharacterRelationship,
                                        relationship_in: CharacterRelationshipUpdate) -> CharacterRelationship:
    """更新人物关系信息，如果相关字段变化则重新生成 Embedding"""
    update_data = relationship_in.model_dump(exclude_unset=True)
    needs_re_embedding = False
    current_data = {}

    embedding_fields = ["relationship_type", "description"]
    for field in embedding_fields:
        if field in update_data:
            current_data[field] = getattr(db_relationship, field)
            if getattr(db_relationship, field) != update_data[field]:
                needs_re_embedding = True
        else:
            current_data[field] = getattr(db_relationship, field)

    # 应用更新
    for key, value in update_data.items():
        setattr(db_relationship, key, value)

    # 如果需要，重新生成并更新 embedding
    if needs_re_embedding:
        text_for_embedding = prepare_text_for_embedding(
            update_data.get("relationship_type", current_data.get("relationship_type")),
            update_data.get("description", current_data.get("description"))
        )
        db_relationship.embedding = await get_embedding(text_for_embedding)

    db.add(db_relationship)
    try:
        db.commit()
        db.refresh(db_relationship)
        return db_relationship
    except IntegrityError:
        db.rollback()
        # 仅当 relationship_type 改变时可能触发唯一约束
        if "relationship_type" in update_data:
            raise ValueError(
                f"A relationship of type '{update_data['relationship_type']}' already exists between these characters (or its inverse).")
        else:
            raise ValueError("Failed to update character relationship due to a database constraint.")


def delete_character_relationship(db: Session, relationship_id: int) -> Optional[CharacterRelationship]:
    """删除人物关系"""
    db_relationship = get_character_relationship(db, relationship_id)
    if db_relationship:
        db.delete(db_relationship)
        db.commit()
    return db_relationship
