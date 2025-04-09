# backend/app/api/routers/settings.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app import schemas
from app.db.session import get_db
from app.services import project_service, setting_service

router = APIRouter()


@router.post("/projects/{project_id}/settings/", response_model=schemas.SettingElementRead,
             status_code=status.HTTP_201_CREATED, tags=["Settings"])
async def create_setting_element_for_project(
        project_id: int,
        setting_in: schemas.SettingElementCreate,  # 输入 schema 不含 project_id
        db: Session = Depends(get_db)
):
    """
    为指定项目创建新设定元素。
    """
    db_project = project_service.get_project(db, project_id=project_id)
    if db_project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Project with id {project_id} not found")

    if setting_in.project_id != project_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Payload project_id ({setting_in.project_id}) does not match URL project_id ({project_id})")

    try:
        setting_element = await setting_service.create_setting_element(db=db, setting=setting_in)
        return setting_element
    except ValueError as e:
        if "already exists" in str(e):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
        elif "Project with id" in str(e):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred.")


@router.get("/projects/{project_id}/settings/", response_model=List[schemas.SettingElementRead], tags=["Settings"])
def read_setting_elements_for_project(
        project_id: int,
        skip: int = 0,
        limit: int = 100,
        db: Session = Depends(get_db)
):
    """
    获取指定项目下的设定元素列表。
    """
    db_project = project_service.get_project(db, project_id=project_id)
    if db_project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Project with id {project_id} not found")

    setting_elements = setting_service.get_setting_elements_by_project(db, project_id=project_id, skip=skip,
                                                                                limit=limit)
    return setting_elements


@router.get("/settings/{setting_element_id}", response_model=schemas.SettingElementRead, tags=["Settings"])
def read_setting_element(
        setting_element_id: int,
        db: Session = Depends(get_db)
):
    """
    获取指定 ID 的设定元素详情。
    """
    db_setting = setting_service.get_setting_element(db, setting_element_id=setting_element_id)
    if db_setting is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Setting element not found")
    return db_setting


@router.patch("/settings/{setting_element_id}", response_model=schemas.SettingElementRead, tags=["Settings"])
async def update_setting_element(
        setting_element_id: int,
        setting_in: schemas.SettingElementUpdate,
        db: Session = Depends(get_db)
):
    """
    更新设定元素信息。会自动重新计算并更新 Embedding (如果相关字段被修改)。
    """
    db_setting = setting_service.get_setting_element(db, setting_element_id=setting_element_id)
    if db_setting is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Setting element not found")

    try:
        updated_setting = await setting_service.update_setting_element(db=db, db_setting=db_setting,
                                                                                setting_in=setting_in)
        return updated_setting
    except ValueError as e:
        if "already exists" in str(e):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="An unexpected error occurred during update.")


@router.delete("/settings/{setting_element_id}", response_model=schemas.SettingElementRead, tags=["Settings"])
def delete_setting_element(
        setting_element_id: int,
        db: Session = Depends(get_db)
):
    """
    删除设定元素。
    注意：与该设定元素关联的 Scene (通过 scene_setting_association) 记录也会被删除。
    """
    deleted_setting = setting_service.delete_setting_element(db, setting_element_id=setting_element_id)
    if deleted_setting is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Setting element not found")
    return deleted_setting
