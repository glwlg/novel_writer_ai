# backend/app/services/chapter_service.py
from sqlalchemy.orm import Session, selectinload
from sqlalchemy.exc import IntegrityError
from sqlalchemy import asc  # 用于排序
from typing import List, Optional

from app.models.structure import Chapter
from app.schemas.chapter import ChapterCreate, ChapterUpdate
from app.services.llm_service import get_embedding, prepare_text_for_embedding


async def create_chapter(db: Session, chapter: ChapterCreate) -> Chapter:
    """创建新章节并生成摘要的 Embedding"""
    embedding_vector = None
    if chapter.summary:  # 只有在提供了摘要时才生成 embedding
        text_for_embedding = prepare_text_for_embedding(chapter.summary)
        embedding_vector = await get_embedding(text_for_embedding)

    db_chapter = Chapter(
        **chapter.model_dump(),
        embedding=embedding_vector  # 添加 embedding (可能为 None)
    )
    db.add(db_chapter)
    try:
        db.commit()
        db.refresh(db_chapter)
        return db_chapter
    except IntegrityError as e:
        db.rollback()
        if "_project_chapter_title_uc" in str(e.orig):
            raise ValueError(f"Chapter with title '{chapter.title}' already exists in this project.")
        elif "projects_fk" in str(e.orig):
            raise ValueError(f"Project with id {chapter.project_id} does not exist.")
        elif "volumes_fk" in str(e.orig):
            raise ValueError(f"Project with id {chapter.volume_id} does not exist.")
        else:
            raise ValueError("Failed to create chapter due to a database constraint.")


def get_chapter(db: Session, chapter_id: int) -> Optional[Chapter]:
    """通过 ID 获取章节，并预加载场景（用于 ChapterRead）"""
    return db.query(Chapter).options(
        selectinload(Chapter.scenes)  # 预加载场景列表
    ).filter(Chapter.id == chapter_id).first()


def get_chapters_by_project(db: Session, project_id: int, skip: int = 0, limit: int = 100) -> List[Chapter]:
    """获取指定项目下的章节列表，按 'order' 排序，并预加载场景"""
    return db.query(Chapter).options(
        selectinload(Chapter.scenes)  # 预加载场景列表
    ).filter(Chapter.project_id == project_id).order_by(
        asc(Chapter.order)  # 按 order 字段升序排序
    ).offset(skip).limit(limit).all()

def get_chapters_by_volume(db: Session, volume_id: int, skip: int = 0, limit: int = 100) -> List[Chapter]:
    """获取指定项目下的章节列表，按 'order' 排序，并预加载场景"""
    return db.query(Chapter).options(
        selectinload(Chapter.scenes)  # 预加载场景列表
    ).filter(Chapter.volume_id == volume_id).order_by(
        asc(Chapter.order)  # 按 order 字段升序排序
    ).offset(skip).limit(limit).all()


async def update_chapter(db: Session, db_chapter: Chapter, chapter_in: ChapterUpdate) -> Chapter:
    """更新章节信息，如果摘要变化则重新生成 Embedding"""
    update_data = chapter_in.model_dump(exclude_unset=True)
    needs_re_embedding = False

    # 检查 summary 是否被更新且内容有变化
    if "summary" in update_data:
        new_summary = update_data["summary"]
        # 只有当新旧摘要不同时才需要重新嵌入（注意处理 None 的情况）
        if new_summary != db_chapter.summary:
            needs_re_embedding = True

    # 应用更新
    for key, value in update_data.items():
        setattr(db_chapter, key, value)

    # 如果需要，重新生成并更新 embedding
    if needs_re_embedding:
        new_summary = db_chapter.summary  # 获取更新后的摘要
        if new_summary:
            text_for_embedding = prepare_text_for_embedding(new_summary)
            db_chapter.embedding = await get_embedding(text_for_embedding)
        else:
            db_chapter.embedding = None  # 如果摘要被清空，则 embedding 也设为 None

    db.add(db_chapter)
    try:
        db.commit()
        db.refresh(db_chapter)
        # 需要重新加载 scenes 关系，因为 refresh 不会加载它们
        db.refresh(db_chapter, attribute_names=['scenes'])  # Pydantic 需要这个
        # 或者重新查询一次: db_chapter = get_chapter(db, db_chapter.id)
        return db_chapter
    except IntegrityError:
        db.rollback()
        # 仅当 title 字段被修改时才可能触发 unique constraint
        if "title" in update_data:
            raise ValueError(f"Chapter with title '{update_data['title']}' already exists in this project.")
        else:
            raise ValueError("Failed to update chapter due to a database constraint.")


def delete_chapter(db: Session, chapter_id: int) -> Optional[Chapter]:
    """删除章节及其下所有场景（通过级联删除）"""
    db_chapter = get_chapter(db, chapter_id)  # 使用 get_chapter 以便返回加载了 scenes 的对象（虽然马上要删除）
    if db_chapter:
        # 在删除前加载关联的 scenes, Pydantic 返回时可能需要? (虽然通常返回删除对象不需要)
        # 如果 ChapterRead 需要返回 scenes，即使是删除操作，也确保已加载
        # 如果不需要，可以直接 db.query(Chapter).filter(Chapter.id == chapter_id).first()
        pass  # get_chapter 已经加载了

        db.delete(db_chapter)
        db.commit()
    return db_chapter
