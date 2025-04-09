# backend/app/api/routers/projects.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app import schemas  # 假设 __init__ 文件处理好了导入
from app.db.session import get_db # 假设 get_db 在这里
from app.services import project_service

router = APIRouter()

@router.post("/projects/", response_model=schemas.ProjectRead, status_code=status.HTTP_201_CREATED, tags=["Projects"])
def create_project(
    project_in: schemas.ProjectCreate,
    db: Session = Depends(get_db)
):
    """
    创建新项目。
    """
    # 可选：检查同名项目是否已存在 (如果需要全局唯一)
    db_project = project_service.get_project_by_title(db, project_title=project_in.title)
    if db_project:
        raise HTTPException(status_code=400, detail="Project with this title already exists")
    return project_service.create_project(db=db, project=project_in)

@router.get("/projects/", response_model=List[schemas.ProjectRead], tags=["Projects"])
def read_projects(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    获取项目列表。
    """
    projects = project_service.get_projects(db, skip=skip, limit=limit)
    return projects

@router.get("/projects/{project_id}", response_model=schemas.ProjectRead, tags=["Projects"])
def read_project(
    project_id: int,
    db: Session = Depends(get_db)
):
    """
    获取指定 ID 的项目详情。
    """
    db_project = project_service.get_project(db, project_id=project_id)
    if db_project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return db_project

@router.patch("/projects/{project_id}", response_model=schemas.ProjectRead, tags=["Projects"])
def update_project(
    project_id: int,
    project_in: schemas.ProjectUpdate,
    db: Session = Depends(get_db)
):
    """
    更新项目信息。
    """
    db_project = project_service.get_project(db, project_id=project_id)
    if db_project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    updated_project = project_service.update_project(db=db, db_project=db_project, project_in=project_in)
    return updated_project

@router.delete("/projects/{project_id}", response_model=schemas.ProjectRead, tags=["Projects"])
def delete_project(
    project_id: int,
    db: Session = Depends(get_db)
):
    """
    删除项目及其所有关联数据（通过级联删除）。
    """
    deleted_project = project_service.delete_project(db, project_id=project_id)
    if deleted_project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    # 注意：返回被删除的对象信息，前端可以确认
    return deleted_project