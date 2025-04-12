# backend/app/services/volume_service.py
from sqlalchemy.orm import Session, selectinload
from sqlalchemy.exc import IntegrityError
from sqlalchemy import asc  # 用于排序
from typing import List, Optional

from app.models.structure import Volume, Chapter
from app.schemas.volume import VolumeCreate, VolumeUpdate
from app.services.llm_service import get_embedding, prepare_text_for_embedding


async def create_volume(db: Session, volume: VolumeCreate) -> Volume:
    """创建新卷并生成摘要的 Embedding"""
    embedding_vector = None
    if volume.summary:  # 只有在提供了摘要时才生成 embedding
        text_for_embedding = prepare_text_for_embedding(volume.summary)
        embedding_vector = await get_embedding(text_for_embedding)

    db_volume = Volume(
        **volume.model_dump(),
        embedding=embedding_vector  # 添加 embedding (可能为 None)
    )
    db.add(db_volume)
    try:
        db.commit()
        db.refresh(db_volume)
        return db_volume
    except IntegrityError as e:
        db.rollback()
        if "_project_volume_title_uc" in str(e.orig):
            raise ValueError(f"Volume with title '{volume.title}' already exists in this project.")
        elif "projects_fk" in str(e.orig):
            raise ValueError(f"Project with id {volume.project_id} does not exist.")
        else:
            raise ValueError("Failed to create volume due to a database constraint.")


def get_volume(db: Session, volume_id: int) -> Optional[Volume]:
    """通过 ID 获取卷，并预加载章节（用于 VolumeRead）"""
    return db.query(Volume).options(
        selectinload(Volume.chapters)  # 预加载章节列表
    ).filter(Volume.id == volume_id).first()


def get_volumes_by_project(db: Session, project_id: int, skip: int = 0, limit: int = 100) -> List[Volume]:
    """获取指定项目下的卷列表，按 'order' 排序，并预加载章节"""
    return db.query(Volume).options(
        selectinload(Volume.chapters)  # 预加载章节列表
    ).filter(Volume.project_id == project_id).order_by(
        asc(Volume.order)  # 按 order 字段升序排序
    ).offset(skip).limit(limit).all()


async def update_volume(db: Session, db_volume: Volume, volume_in: VolumeUpdate) -> Volume:
    """更新卷信息，如果摘要变化则重新生成 Embedding"""
    update_data = volume_in.model_dump(exclude_unset=True)
    needs_re_embedding = False

    # 检查 summary 是否被更新且内容有变化
    if "summary" in update_data:
        new_summary = update_data["summary"]
        # 只有当新旧摘要不同时才需要重新嵌入（注意处理 None 的情况）
        if new_summary != db_volume.summary:
            needs_re_embedding = True

    # 应用更新
    for key, value in update_data.items():
        setattr(db_volume, key, value)

    # 如果需要，重新生成并更新 embedding
    if needs_re_embedding:
        new_summary = db_volume.summary  # 获取更新后的摘要
        if new_summary:
            text_for_embedding = prepare_text_for_embedding(new_summary)
            db_volume.embedding = await get_embedding(text_for_embedding)
        else:
            db_volume.embedding = None  # 如果摘要被清空，则 embedding 也设为 None

    db.add(db_volume)
    try:
        db.commit()
        db.refresh(db_volume)
        # 需要重新加载 chapters 关系，因为 refresh 不会加载它们
        db.refresh(db_volume, attribute_names=['chapters'])  # Pydantic 需要这个
        # 或者重新查询一次: db_volume = get_volume(db, db_volume.id)
        return db_volume
    except IntegrityError:
        db.rollback()
        # 仅当 title 字段被修改时才可能触发 unique constraint
        if "title" in update_data:
            raise ValueError(f"Volume with title '{update_data['title']}' already exists in this project.")
        else:
            raise ValueError("Failed to update volume due to a database constraint.")


def delete_volume(db: Session, volume_id: int) -> Optional[Volume]:
    """删除卷及其下所有章节（通过级联删除）"""
    db_volume = get_volume(db, volume_id)  # 使用 get_volume 以便返回加载了 chapters 的对象（虽然马上要删除）
    if db_volume:
        # 在删除前加载关联的 chapters, Pydantic 返回时可能需要? (虽然通常返回删除对象不需要)
        # 如果 VolumeRead 需要返回 chapters，即使是删除操作，也确保已加载
        # 如果不需要，可以直接 db.query(Volume).filter(Volume.id == volume_id).first()
        pass  # get_volume 已经加载了

        db.delete(db_volume)
        db.commit()
    return db_volume
