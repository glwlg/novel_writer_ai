# backend/app/api/routers/characters.py
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import schemas
from app.db.session import get_db
from app.services import project_service, character_service

router = APIRouter()

# 使用项目 ID 作为路径前缀更符合 RESTful 风格
@router.post("/projects/{project_id}/characters/", response_model=schemas.CharacterRead, status_code=status.HTTP_201_CREATED, tags=["Characters"])
async def create_character_for_project(
    project_id: int,
    character_in: schemas.CharacterCreate, # 注意：输入 schema 不应包含 project_id
    db: Session = Depends(get_db)
):
    """
    为指定项目创建新角色。
    """
    # 1. 验证项目是否存在
    db_project = project_service.get_project(db, project_id=project_id)
    if db_project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Project with id {project_id} not found")

    # 2. 确保传入的 project_id 与 URL 中的一致 (或直接使用 URL 中的)
    if character_in.project_id != project_id:
         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                             detail=f"Payload project_id ({character_in.project_id}) does not match URL project_id ({project_id})")

    try:
        character = await character_service.create_character(db=db, character=character_in)
        return character
    except ValueError as e:
        # 捕获 CRUD 层抛出的特定错误
        if "already exists" in str(e):
             raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
        elif "Project with id" in str(e) or "does not exist" in str(e):
             raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) # 或者 400 Bad Request
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e: # 其他意外错误
         # Log the error e
         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred.")


@router.get("/projects/{project_id}/characters/", response_model=List[schemas.CharacterRead], tags=["Characters"])
def read_characters_for_project(
    project_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    获取指定项目下的角色列表。
    """
    # 验证项目是否存在 (可选，如果确信 project_id 有效)
    db_project = project_service.get_project(db, project_id=project_id)
    if db_project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Project with id {project_id} not found")

    characters = character_service.get_characters_by_project(db, project_id=project_id, skip=skip, limit=limit)
    return characters

@router.get("/characters/{character_id}", response_model=schemas.CharacterRead, tags=["Characters"])
def read_character(
    character_id: int,
    db: Session = Depends(get_db)
):
    """
    获取指定 ID 的角色详情。
    """
    db_character = character_service.get_character(db, character_id=character_id)
    if db_character is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Character not found")
    return db_character

@router.patch("/characters/{character_id}", response_model=schemas.CharacterRead, tags=["Characters"])
async def update_character(
    character_id: int,
    character_in: schemas.CharacterUpdate,
    db: Session = Depends(get_db)
):
    """
    更新角色信息。会自动重新计算并更新 Embedding (如果相关字段被修改)。
    """
    db_character = character_service.get_character(db, character_id=character_id)
    if db_character is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Character not found")

    # 检查是否尝试修改 project_id (通常不允许)
    # if character_in.project_id is not None and character_in.project_id != db_character.project_id:
    #    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot change the project_id of a character.")

    try:
        updated_character = await character_service.update_character(db=db, db_character=db_character, character_in=character_in)
        return updated_character
    except ValueError as e:
        if "already exists" in str(e):
             raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
         # Log the error e
         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred during update.")


@router.delete("/characters/{character_id}", response_model=schemas.CharacterRead, tags=["Characters"])
def delete_character(
    character_id: int,
    db: Session = Depends(get_db)
):
    """
    删除角色。
    注意：与该角色相关的 CharacterRelationship 也会因级联设置而被删除。
    注意：与该角色关联的 Scene (通过 scene_character_association) 记录也会被删除。
    """
    deleted_character = character_service.delete_character(db, character_id=character_id)
    if deleted_character is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Character not found")
    return deleted_character