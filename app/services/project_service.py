# backend/app/services/project_service.py
from sqlalchemy.orm import Session
from typing import List, Optional

from app.models.project import Project
from app.schemas.project import ProjectCreate, ProjectUpdate


def get_project_by_title(db: Session, project_title: str) -> Optional[Project]:
    """通过 title 获取项目"""
    return db.query(Project).filter(Project.title == project_title).first()

def get_project(db: Session, project_id: int) -> Optional[Project]:
    """通过 ID 获取项目"""
    return db.query(Project).filter(Project.id == project_id).first()


def get_projects(db: Session, skip: int = 0, limit: int = 100) -> List[Project]:
    """获取项目列表（分页）"""
    return db.query(Project).offset(skip).limit(limit).all()


def create_project(db: Session, project: ProjectCreate) -> Project:
    """创建新项目"""
    db_project = Project(**project.model_dump())
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project


def update_project(db: Session, db_project: Project, project_in: ProjectUpdate) -> Project:
    """更新项目信息"""
    update_data = project_in.model_dump(exclude_unset=True)  # 只获取传入的字段
    for key, value in update_data.items():
        setattr(db_project, key, value)
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project


def delete_project(db: Session, project_id: int) -> Optional[Project]:
    """删除项目"""
    db_project = get_project(db, project_id)
    if db_project:
        db.delete(db_project)
        db.commit()
    return db_project  # 返回被删除的对象，或 None
