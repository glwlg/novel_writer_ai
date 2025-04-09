# backend/app/routers/generation.py
from fastapi import APIRouter, Depends, HTTPException, status, Path
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas import SceneRead  # Use the detailed read schema
from app.services.rag_service import generate_scene_content_rag  # Import the core function

router = APIRouter()

@router.post(
    "/scenes/{scene_id}/generate_rag",
    response_model=SceneRead, # Return the updated scene data
    status_code=status.HTTP_200_OK,
    summary="Generate Scene Content using RAG",
    description="Triggers the RAG process to generate narrative content for a specific scene based on its goal and relevant project context.",
    tags=["Generation"] # Add a tag for Swagger UI grouping
)
async def generate_scene_rag_endpoint(
    *, # Makes subsequent arguments keyword-only
    db: Session = Depends(get_db),
    scene_id: int = Path(..., title="The ID of the scene to generate content for", ge=1)
):
    """
    Initiates the Retrieval-Augmented Generation (RAG) process for the specified scene.

    - Fetches the scene's goal.
    - Retrieves relevant characters, settings, and relationships from the project using vector similarity.
    - Constructs a prompt combining the goal and context.
    - Calls the configured LLM to generate the scene's narrative content.
    - Updates the scene's `generated_content`, sets its status to `drafted`,
      and optionally generates/stores a summary and its embedding.

    Requires a valid `scene_id` and that the scene has a defined `goal`.
    The LLM service must be configured correctly (e.g., OpenAI API key).
    """
    try:
        updated_scene = await generate_scene_content_rag(
            db=db,
            scene_id=scene_id
        )
        # Pydantic will automatically validate and convert the ORM object
        # to the SceneRead schema based on the response_model
        return updated_scene
    except HTTPException as http_exc:
        # Re-raise known HTTP exceptions (e.g., 404 Not Found, 400 Bad Request from service)
        raise http_exc
    except Exception as e:
        # Catch unexpected errors from the service layer
        # Log the error for debugging
        print(f"Unexpected error in generate_scene_rag_endpoint for scene {scene_id}: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal server error occurred while generating scene content."
        )