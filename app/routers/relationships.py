# backend/app/api/routers/relationships.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app import schemas
from app.db.session import get_db
from app.services import relationship_service, project_service, character_service

router = APIRouter()


@router.post("/projects/{project_id}/relationships/", response_model=schemas.CharacterRelationshipRead,
             status_code=status.HTTP_201_CREATED, tags=["Relationships"])
async def create_character_relationship_for_project(
        project_id: int,
        relationship_in: schemas.CharacterRelationshipCreate,  # 输入 schema 含 project_id
        db: Session = Depends(get_db)
):
    """
    为指定项目创建新的人物关系。
    需要提供 character1_id, character2_id, relationship_type。
    会自动校验角色是否存在且属于该项目。
    """
    # 校验 project_id 匹配
    if relationship_in.project_id != project_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Payload project_id ({relationship_in.project_id}) does not match URL project_id ({project_id})")

    # project 存在性校验依赖外键或 crud 函数内部校验

    try:
        relationship = await relationship_service.create_character_relationship(db=db,
                                                                                         relationship=relationship_in)
        return relationship
    except ValueError as e:
        # 捕获 CRUD 层抛出的特定错误
        if "already exists" in str(e):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
        elif "not found" in str(e) or "Invalid character" in str(e) or "must belong" in str(
                e) or "same character" in str(e):
            # 这些错误通常是客户端输入问题
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred.")


@router.get("/projects/{project_id}/relationships/", response_model=List[schemas.CharacterRelationshipRead],
            tags=["Relationships"])
def read_relationships_for_project(
        project_id: int,
        character_id: Optional[int] = Query(None, description="Filter relationships involving this character ID"),
        # 可选过滤
        skip: int = 0,
        limit: int = 100,
        db: Session = Depends(get_db)
):
    """
    获取指定项目下的人物关系列表。
    可以根据 character_id 进行过滤。
    """
    db_project = project_service.get_project(db, project_id=project_id)
    if db_project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Project with id {project_id} not found")

    if character_id:
        # 验证 character_id 是否属于 project_id (可选但推荐)
        db_char = character_service.get_character(db, character_id)
        if not db_char or db_char.project_id != project_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"Character with id {character_id} not found in project {project_id}")
        relationships = relationship_service.get_relationships_for_character(db, character_id=character_id)
        # 注意：分页逻辑需要调整，如果基于 character_id 过滤
        # 这里简单返回所有，实际可能需要对结果进行分页
        return relationships[skip: skip + limit]
    else:
        relationships = relationship_service.get_relationships_by_project(db, project_id=project_id, skip=skip,
                                                                                   limit=limit)
        return relationships


@router.get("/relationships/{relationship_id}", response_model=schemas.CharacterRelationshipRead,
            tags=["Relationships"])
def read_character_relationship(
        relationship_id: int,
        db: Session = Depends(get_db)
):
    """
    获取指定 ID 的人物关系详情。
    """
    db_relationship = relationship_service.get_character_relationship(db, relationship_id=relationship_id)
    if db_relationship is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Character relationship not found")
    return db_relationship


@router.patch("/relationships/{relationship_id}", response_model=schemas.CharacterRelationshipRead,
              tags=["Relationships"])
async def update_character_relationship(
        relationship_id: int,
        relationship_in: schemas.CharacterRelationshipUpdate,
        db: Session = Depends(get_db)
):
    """
    更新人物关系信息 (通常只更新 type 和 description)。
    会自动重新计算并更新 Embedding (如果相关字段被修改)。
    """
    db_relationship = relationship_service.get_character_relationship(db, relationship_id=relationship_id)
    if db_relationship is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Character relationship not found")

    try:
        updated_relationship = await relationship_service.update_character_relationship(db=db,
                                                                                                 db_relationship=db_relationship,
                                                                                                 relationship_in=relationship_in)
        return updated_relationship
    except ValueError as e:
        if "already exists" in str(e):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="An unexpected error occurred during update.")


@router.delete("/relationships/{relationship_id}", response_model=schemas.CharacterRelationshipRead,
               tags=["Relationships"])
def delete_character_relationship(
        relationship_id: int,
        db: Session = Depends(get_db)
):
    """
    删除人物关系。
    """
    deleted_relationship = relationship_service.delete_character_relationship(db,
                                                                                       relationship_id=relationship_id)
    if deleted_relationship is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Character relationship not found")
    return deleted_relationship
