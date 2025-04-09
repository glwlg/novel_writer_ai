# backend/app/services/scene_service.py

from typing import Optional, Sequence, List

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import Scene, Project, Chapter  # Assuming models are correctly imported
from app.schemas import SceneCreate, SceneUpdate
from app.schemas.scene import SceneUpdateGenerated
from app.services import llm_service


async def _generate_and_set_goal_embedding(db: Session, scene: Scene):
    """Internal helper to generate and set goal embedding."""
    if scene.goal:
        try:
            # IMPORTANT: Call the actual embedding function here
            goal_embedding = await llm_service.get_embedding(scene.goal)
            scene.goal_embedding = goal_embedding
            # No commit here, assumes caller will commit
        except Exception as e:
            print(f"Error generating embedding for scene {scene.id} goal: {e}")  # Replace with proper logging
            scene.goal_embedding = None  # Clear or leave as is? Decide policy.
    else:
        scene.goal_embedding = None


async def create_scene(db: Session, scene: SceneCreate) -> Scene:
    """Creates a new Scene, associated with a Project and optionally a Chapter."""
    # Check if project exists
    project = db.get(Project, scene.project_id)
    if not project:
        raise ValueError(f"Project with id {scene.project_id} not found")

    # Check if chapter exists if chapter_id is provided
    if scene.chapter_id:
        chapter = db.get(Chapter, scene.chapter_id)
        if not chapter:
            raise ValueError(f"Chapter with id {scene.chapter_id} not found")
        # Optional: Check if chapter belongs to the same project
        if chapter.project_id != scene.project_id:
            raise ValueError(f"Chapter {scene.chapter_id} does not belong to Project {scene.project_id}")

    # Create the Scene instance
    db_scene = Scene(**scene.model_dump(exclude_unset=True))
    # generated_content, summary, summary_embedding are initially None/default

    # Generate goal embedding *before* first commit if possible
    await _generate_and_set_goal_embedding(db, db_scene)

    db.add(db_scene)
    db.commit()
    db.refresh(db_scene)
    return db_scene


def get_scene(db: Session, scene_id: int) -> Optional[Scene]:
    """Gets a single scene by ID."""
    return db.query(Scene).options(
        selectinload(Scene.project)
    ).filter(Scene.id == scene_id).first()


def get_scenes_by_chapter(db: Session, chapter_id: int, skip: int = 0, limit: int = 100) -> List[Scene]:
    """Gets all scenes for a specific chapter, ordered by 'order_in_chapter'."""
    # Check if chapter exists
    chapter = db.get(Chapter, chapter_id)
    if not chapter:
        raise ValueError(f"Chapter with id {chapter_id} not found")

    return db.query(Scene).filter(
        Scene.chapter_id == chapter_id).order_by(Scene.order_in_chapter).all()


def get_scenes_by_project_unassigned(db: Session, project_id: int, skip: int = 0, limit: int = 100) -> Sequence[
    Scene]:
    """Gets scenes belonging to a project but not assigned to any chapter."""
    # Check if project exists
    project = db.get(Project, project_id)
    if not project:
        raise ValueError(f"Project with id {project_id} not found")

    return db.query(Scene).filter(
        Scene.project_id == project_id, Scene.chapter_id == None).order_by(
        Scene.created_at).offset(skip).limit(limit).all()


async def update_scene_generated(db: Session, scene_id: int, scene_update: SceneUpdateGenerated) -> Optional[Scene]:
    """更新场景的生成内容和状态。"""
    db_scene = get_scene(db, scene_id)
    if not db_scene:
        return None
    update_data = scene_update.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        current_value = getattr(db_scene, key)
        if current_value != value:
            setattr(db_scene, key, value)

    db.add(db_scene)
    db.commit()
    db.refresh(db_scene)
    return db_scene


async def update_scene_metadata(db: Session, scene_id: int, scene_update: SceneUpdate) -> Optional[Scene]:
    """Updates an existing scene's metadata (excluding generated content)."""
    db_scene = get_scene(db, scene_id)
    if not db_scene:
        return None

    update_data = scene_update.model_dump(exclude_unset=True)
    needs_embedding_update = False

    # Check if chapter is being changed and validate new chapter
    if 'chapter_id' in update_data and update_data['chapter_id'] is not None:
        new_chapter = db.get(Chapter, update_data['chapter_id'])
        if not new_chapter:
            raise ValueError(f"Target Chapter with id {update_data['chapter_id']} not found")
        if new_chapter.project_id != db_scene.project_id:
            raise ValueError(
                f"Target Chapter {update_data['chapter_id']} does not belong to the scene's Project {db_scene.project_id}")

    for key, value in update_data.items():
        current_value = getattr(db_scene, key)
        if current_value != value:
            setattr(db_scene, key, value)
            if key == 'goal':
                needs_embedding_update = True

    if needs_embedding_update:
        await _generate_and_set_goal_embedding(db, db_scene)

    db.add(db_scene)  # Add to session context if detached
    db.commit()
    db.refresh(db_scene)
    return db_scene


def delete_scene(db: Session, scene_id: int) -> Optional[Scene]:
    """Deletes a scene."""
    db_scene = db.get(Scene, scene_id)
    if db_scene:
        db.delete(db_scene)
        db.commit()
    return db_scene
