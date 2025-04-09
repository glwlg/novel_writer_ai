# backend/app/services/setting_service.py
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List, Optional

from app.models.setting import SettingElement
from app.schemas.setting import SettingElementCreate, SettingElementUpdate
from app.services.llm_service import get_embedding, prepare_text_for_embedding


async def create_setting_element(db: Session, setting: SettingElementCreate) -> SettingElement:
    """创建新设定元素并生成 Embedding"""
    text_for_embedding = prepare_text_for_embedding(setting.name, setting.description)
    embedding_vector = await get_embedding(text_for_embedding)

    db_setting = SettingElement(
        **setting.model_dump(),
        embedding=embedding_vector
    )
    db.add(db_setting)
    try:
        db.commit()
        db.refresh(db_setting)
        return db_setting
    except IntegrityError as e:
        db.rollback()
        if "uq_project_setting_name_type" in str(e.orig):
            raise ValueError(
                f"Setting element with name '{setting.name}' and type '{setting.element_type}' already exists in this project.")
        elif "projects_fk" in str(e.orig):
            raise ValueError(f"Project with id {setting.project_id} does not exist.")
        else:
            raise ValueError("Failed to create setting element due to a database constraint.")


def get_setting_element(db: Session, setting_element_id: int) -> Optional[SettingElement]:
    """通过 ID 获取设定元素"""
    return db.query(SettingElement).filter(SettingElement.id == setting_element_id).first()


def get_setting_elements_by_project(db: Session, project_id: int, skip: int = 0, limit: int = 100) -> List[
    SettingElement]:
    """获取指定项目下的设定元素列表（分页）"""
    return db.query(SettingElement).filter(SettingElement.project_id == project_id).offset(skip).limit(limit).all()


async def update_setting_element(db: Session, db_setting: SettingElement,
                                 setting_in: SettingElementUpdate) -> SettingElement:
    """更新设定元素信息，如果相关字段变化则重新生成 Embedding"""
    update_data = setting_in.model_dump(exclude_unset=True)
    needs_re_embedding = False
    current_data = {}

    embedding_fields = ["name", "description"]
    for field in embedding_fields:
        if field in update_data:
            current_data[field] = getattr(db_setting, field)
            if getattr(db_setting, field) != update_data[field]:
                needs_re_embedding = True
        else:
            current_data[field] = getattr(db_setting, field)

    # 应用更新
    for key, value in update_data.items():
        setattr(db_setting, key, value)

    # 如果需要，重新生成并更新 embedding
    if needs_re_embedding:
        text_for_embedding = prepare_text_for_embedding(
            update_data.get("name", current_data.get("name")),
            update_data.get("description", current_data.get("description"))
        )
        db_setting.embedding = await get_embedding(text_for_embedding)

    db.add(db_setting)
    try:
        db.commit()
        db.refresh(db_setting)
        return db_setting
    except IntegrityError:
        db.rollback()
        # 仅当 name 或 element_type 改变时可能触发
        if "name" in update_data or "element_type" in update_data:
            updated_name = update_data.get("name", db_setting.name)
            updated_type = update_data.get("element_type", db_setting.element_type)
            raise ValueError(
                f"Setting element with name '{updated_name}' and type '{updated_type}' already exists in this project.")
        else:
            raise ValueError("Failed to update setting element due to a database constraint.")


def delete_setting_element(db: Session, setting_element_id: int) -> Optional[SettingElement]:
    """删除设定元素"""
    db_setting = get_setting_element(db, setting_element_id)
    if db_setting:
        db.delete(db_setting)
        db.commit()
    return db_setting
