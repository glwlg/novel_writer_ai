# backend/app/service/character_service.py
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List, Optional

from app.models.character import Character
from app.schemas.character import CharacterCreate, CharacterUpdate
from app.services.llm_service import get_embedding, prepare_text_for_embedding # 导入 Embedding 服务

async def create_character(db: Session, character: CharacterCreate) -> Character:
    """创建新角色并生成 Embedding"""
    # 准备用于 Embedding 的文本
    text_for_embedding = prepare_text_for_embedding(
        character.name,
        character.description,
        character.backstory,
        character.goals,
        character.arc_summary
    )
    embedding_vector = await get_embedding(text_for_embedding)

    db_character = Character(
        **character.model_dump(),
        embedding=embedding_vector # 添加 embedding
    )
    db.add(db_character)
    try:
        db.commit()
        db.refresh(db_character)
        return db_character
    except IntegrityError as e:
        db.rollback() # 回滚事务
        # 可以更精细地判断是哪个约束冲突，这里简单处理
        if "uq_project_character_name" in str(e.orig): # 检查是否是名称唯一约束
             raise ValueError(f"Character with name '{character.name}' already exists in this project.")
        elif "projects_fk" in str(e.orig): # 检查外键约束
             raise ValueError(f"Project with id {character.project_id} does not exist.")
        else:
            raise ValueError("Failed to create character due to a database constraint.") # 其他约束错误


def get_character(db: Session, character_id: int) -> Optional[Character]:
    """通过 ID 获取角色"""
    return db.query(Character).filter(Character.id == character_id).first()

def get_characters_by_project(db: Session, project_id: int, skip: int = 0, limit: int = 100) -> List[Character]:
    """获取指定项目下的角色列表（分页）"""
    return db.query(Character).filter(Character.project_id == project_id).offset(skip).limit(limit).all()

async def update_character(db: Session, db_character: Character, character_in: CharacterUpdate) -> Character:
    """更新角色信息，如果相关字段变化则重新生成 Embedding"""
    update_data = character_in.model_dump(exclude_unset=True)
    needs_re_embedding = False
    current_data = {}

    # 检查是否有需要 embedding 的字段被更新
    embedding_fields = ["name", "description", "backstory", "goals", "arc_summary"]
    for field in embedding_fields:
        if field in update_data:
            current_data[field] = getattr(db_character, field) # 保存旧值以便比较
            if getattr(db_character, field) != update_data[field]:
                 needs_re_embedding = True
        else:
            # 如果字段未在更新数据中，使用数据库中的当前值
             current_data[field] = getattr(db_character, field)


    # 应用更新
    for key, value in update_data.items():
        setattr(db_character, key, value)

    # 如果需要，重新生成并更新 embedding
    if needs_re_embedding:
        text_for_embedding = prepare_text_for_embedding(
            update_data.get("name", current_data.get("name")), # 使用更新后的值（如果存在）
            update_data.get("description", current_data.get("description")),
            update_data.get("backstory", current_data.get("backstory")),
            update_data.get("goals", current_data.get("goals")),
            update_data.get("arc_summary", current_data.get("arc_summary"))
        )
        db_character.embedding = await get_embedding(text_for_embedding)

    db.add(db_character)
    try:
        db.commit()
        db.refresh(db_character)
        return db_character
    except IntegrityError:
        db.rollback()
        # 仅当 name 字段被修改时才可能触发 unique constraint
        if "name" in update_data:
            raise ValueError(f"Character with name '{update_data['name']}' already exists in this project.")
        else:
             raise ValueError("Failed to update character due to a database constraint.")


def delete_character(db: Session, character_id: int) -> Optional[Character]:
    """删除角色"""
    db_character = get_character(db, character_id)
    if db_character:
        db.delete(db_character)
        db.commit()
    return db_character