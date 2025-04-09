# backend/app/routers/chapters.py

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas import ChapterCreate, ChapterRead, ChapterUpdate  # Make sure ChapterReadMinimal is imported if used
from app.services import chapter_service

router = APIRouter()


# Define path operations for Chapters

@router.post("/projects/{project_id}/chapters", response_model=ChapterRead, status_code=status.HTTP_201_CREATED)
async def create_new_chapter(
        project_id: int,
        chapter: ChapterCreate,
        db: Session = Depends(get_db)
):
    """
    Create a new chapter for a specific project.
    Requires project_id in the path and chapter data in the body.
    Ensures the created chapter belongs to the specified project.
    """
    # Ensure the project_id in the path matches the one potentially in the body (or enforce path only)
    if chapter.project_id != project_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Project ID in path does not match project_id in request body."
        )
    try:
        created_chapter = await chapter_service.create_chapter(db=db, chapter=chapter)
        return created_chapter
    except ValueError as e:  # Catch specific errors from service layer
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:  # Catch potential db constraint errors etc.
        # Log the exception e
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail=f"Could not create chapter. Possible duplicate title or invalid data: {e}")


@router.get("/projects/{project_id}/chapters", response_model=List[ChapterRead])  # Use ChapterRead to include scenes
async def read_project_chapters(
        project_id: int,
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=200),
        db: Session = Depends(get_db)
):
    """
    Retrieve all chapters for a specific project, ordered by their 'order' field.
    Includes minimal scene information nested within each chapter.
    """
    try:
        chapters = chapter_service.get_chapters_by_project(db=db, project_id=project_id, skip=skip, limit=limit)
        return chapters
    except ValueError as e:  # Project not found from service
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/chapters/{chapter_id}", response_model=ChapterRead)
async def read_single_chapter(
        chapter_id: int = Path(..., description="The ID of the chapter to retrieve"),
        db: Session = Depends(get_db)
):
    """
    Retrieve a single chapter by its ID. Includes minimal scene information.
    """
    db_chapter = chapter_service.get_chapter(db=db, chapter_id=chapter_id)
    if db_chapter is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chapter not found")
    return db_chapter


@router.patch("/chapters/{chapter_id}", response_model=ChapterRead)
async def update_existing_chapter(
        chapter_id: int,
        chapter_update: ChapterUpdate,
        db: Session = Depends(get_db)
):
    db_chapter = chapter_service.get_chapter(db, chapter_id=chapter_id)
    if db_chapter is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chapter not found")
    """
    Update an existing chapter's details (title, summary, order).
    """
    updated_chapter = await chapter_service.update_chapter(db=db, db_chapter=db_chapter, chapter_in=chapter_update)
    if updated_chapter is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chapter not found")
    # Check for potential conflicts during update if necessary (e.g., unique constraints)
    # For simplicity, assuming service layer handles basic validation or DB raises errors
    return updated_chapter


@router.delete("/chapters/{chapter_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_chapter(
        chapter_id: int,
        db: Session = Depends(get_db)
):
    """
    Delete a chapter by its ID. Associated scenes will also be deleted due to cascade.
    """
    deleted_chapter = await chapter_service.delete_chapter(db=db, chapter_id=chapter_id)
    if deleted_chapter is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chapter not found")
    return None  # Return No Content on successful deletion
