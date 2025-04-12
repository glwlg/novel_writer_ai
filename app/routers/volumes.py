# backend/app/routers/volumes.py

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas import VolumeCreate, VolumeRead, VolumeUpdate  # Make sure VolumeReadMinimal is imported if used
from app.services import volume_service

router = APIRouter()


# Define path operations for Volumes

@router.post("/projects/{project_id}/volumes", response_model=VolumeRead, status_code=status.HTTP_201_CREATED)
async def create_new_volume(
        project_id: int,
        volume: VolumeCreate,
        db: Session = Depends(get_db)
):
    """
    Create a new volume for a specific project.
    Requires project_id in the path and volume data in the body.
    Ensures the created volume belongs to the specified project.
    """
    # Ensure the project_id in the path matches the one potentially in the body (or enforce path only)
    if volume.project_id != project_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Project ID in path does not match project_id in request body."
        )
    try:
        created_volume = await volume_service.create_volume(db=db, volume=volume)
        return created_volume
    except ValueError as e:  # Catch specific errors from service layer
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:  # Catch potential db constraint errors etc.
        # Log the exception e
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail=f"Could not create volume. Possible duplicate title or invalid data: {e}")


@router.get("/projects/{project_id}/volumes", response_model=List[VolumeRead])  # Use VolumeRead to include chapters
async def read_project_volumes(
        project_id: int,
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=200),
        db: Session = Depends(get_db)
):
    """
    Retrieve all volumes for a specific project, ordered by their 'order' field.
    Includes minimal scene information nested within each volume.
    """
    try:
        volumes = volume_service.get_volumes_by_project(db=db, project_id=project_id, skip=skip, limit=limit)
        return volumes
    except ValueError as e:  # Project not found from service
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/volumes/{volume_id}", response_model=VolumeRead)
async def read_single_volume(
        volume_id: int = Path(..., description="The ID of the volume to retrieve"),
        db: Session = Depends(get_db)
):
    """
    Retrieve a single volume by its ID. Includes minimal scene information.
    """
    db_volume = volume_service.get_volume(db=db, volume_id=volume_id)
    if db_volume is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Volume not found")
    return db_volume


@router.patch("/volumes/{volume_id}", response_model=VolumeRead)
async def update_existing_volume(
        volume_id: int,
        volume_update: VolumeUpdate,
        db: Session = Depends(get_db)
):
    db_volume = volume_service.get_volume(db, volume_id=volume_id)
    if db_volume is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Volume not found")
    """
    Update an existing volume's details (title, summary, order).
    """
    updated_volume = await volume_service.update_volume(db=db, db_volume=db_volume, volume_in=volume_update)
    if updated_volume is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Volume not found")
    # Check for potential conflicts during update if necessary (e.g., unique constraints)
    # For simplicity, assuming service layer handles basic validation or DB raises errors
    return updated_volume


@router.delete("/volumes/{volume_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_volume(
        volume_id: int,
        db: Session = Depends(get_db)
):
    """
    Delete a volume by its ID. Associated chapters will also be deleted due to cascade.
    """
    deleted_volume = await volume_service.delete_volume(db=db, volume_id=volume_id)
    if deleted_volume is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Volume not found")
    return None  # Return No Content on successful deletion
