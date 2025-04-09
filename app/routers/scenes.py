# backend/app/routers/scenes.py

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas import SceneCreate, SceneRead, SceneUpdate, SceneReadMinimal
from app.services import scene_service

router = APIRouter()


# Define path operations for Scenes (Metadata CRUD)

@router.post("/scenes", response_model=SceneRead, status_code=status.HTTP_201_CREATED)
async def create_new_scene(
        scene: SceneCreate,
        db: Session = Depends(get_db)
):
    """
    Create a new scene record. Requires project_id and goal.
    Can optionally be assigned to a chapter_id.
    Generates and stores embedding for the scene's goal.
    """
    try:
        created_scene = await scene_service.create_scene(db=db, scene=scene)
        return created_scene
    except ValueError as e:  # Catch specific errors like Project/Chapter not found
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        # Log e
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Could not create scene: {e}")


@router.get("/chapters/{chapter_id}/scenes", response_model=List[SceneReadMinimal])
async def read_chapter_scenes(
        chapter_id: int,
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=200),
        db: Session = Depends(get_db)
):
    """
    Retrieve scenes belonging to a specific chapter, ordered by their order_in_chapter.
    Returns minimal scene details suitable for lists.
    """
    try:
        scenes = scene_service.get_scenes_by_chapter(db=db, chapter_id=chapter_id, skip=skip, limit=limit)
        return scenes
    except ValueError as e:  # Chapter not found
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/projects/{project_id}/scenes/unassigned", response_model=List[SceneReadMinimal])
async def read_unassigned_project_scenes(
        project_id: int,
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=200),
        db: Session = Depends(get_db)
):
    """
    Retrieve scenes belonging to a project that are not assigned to any chapter.
    """
    try:
        scenes = scene_service.get_scenes_by_project_unassigned(db=db, project_id=project_id, skip=skip,
                                                                      limit=limit)
        return scenes
    except ValueError as e:  # Project not found
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/scenes/{scene_id}", response_model=SceneRead)
async def read_single_scene(
        scene_id: int = Path(..., description="The ID of the scene to retrieve"),
        db: Session = Depends(get_db)
):
    """
    Retrieve the full details of a single scene by its ID.
    """
    db_scene = scene_service.get_scene(db=db, scene_id=scene_id)
    if db_scene is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scene not found")
    return db_scene


@router.patch("/scenes/{scene_id}", response_model=SceneRead)
async def update_scene_metadata_endpoint(
        scene_id: int,
        scene_update: SceneUpdate,
        db: Session = Depends(get_db)
):
    """
    Update an existing scene's metadata (e.g., title, goal, order, status, chapter_id).
    If the 'goal' is updated, its embedding will be regenerated.
    Note: This endpoint does *not* update generated_content.
    """
    try:
        updated_scene = await scene_service.update_scene_metadata(db=db, scene_id=scene_id, scene_update=scene_update)
        if updated_scene is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scene not found")
        return updated_scene
    except ValueError as e:  # Catch errors like chapter validation
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        # Log e
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Could not update scene: {e}")


@router.delete("/scenes/{scene_id}", response_model=SceneRead, tags=["Scenes"])
def delete_existing_scene(
        scene_id: int,
        db: Session = Depends(get_db)
):
    """
    Delete a scene by its ID.
    """
    deleted_scene = scene_service.delete_scene(db=db, scene_id=scene_id)
    if deleted_scene is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scene not found")
    return deleted_scene
