# 在你的 RAG 服务函数内部
from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.models import Character, CharacterRelationship, SettingElement, Scene, Chapter
from sqlalchemy.orm import Session, selectinload
from typing import List, Dict, Any, Optional

from app.models.structure import SceneStatus
from app.schemas import SceneUpdate
from app.schemas.scene import SceneUpdateGenerated
from app.services import llm_service, scene_service


# --- 检索函数 ---

async def retrieve_relevant_context(
        db: Session,
        project_id: int,
        query_embedding: List[float],
        k_per_type: int,  # 每个类别检索多少条
        current_scene_id: Optional[int] = None  # 用于排除正在生成的场景自身
) -> Dict[str, List[Any]]:
    """
    从数据库检索与查询向量相关的上下文信息。

    Args:
        project_id: 当前项目的 ID。
        query_embedding: 查询文本（如场景目标）的向量。
        k_per_type: 每个信息类别（角色、设定、场景等）最多检索的条数。
        db: SQLAlchemy 数据库会话。
        current_scene_id: (可选) 当前正在处理的场景 ID，用于从检索中排除。

    Returns:
        一个字典，键是上下文类别（如 'characters', 'settings', 'past_scenes'），
        值是检索到的 SQLAlchemy 模型对象列表。
    """
    retrieved_context = {
        "characters": [],
        "settings": [],
        "past_scenes": [],
        "character_relationships": [],
        "chapters": [],
    }
    print(f"Starting context retrieval for project {project_id} with k={k_per_type}")

    # 1. 检索相关角色
    try:
        relevant_characters = db.query(Character) \
            .filter(Character.project_id == project_id, Character.embedding != None) \
            .order_by(Character.embedding.cosine_distance(query_embedding)) \
            .limit(k_per_type) \
            .all()
        retrieved_context["characters"] = relevant_characters
        print(f"Retrieved {len(relevant_characters)} relevant characters.")
    except Exception as e:
        print(f"Error retrieving characters: {e}")  # 添加错误处理

    # 2. 检索相关设定
    try:
        relevant_settings = db.query(SettingElement) \
            .filter(SettingElement.project_id == project_id, SettingElement.embedding != None) \
            .order_by(SettingElement.embedding.cosine_distance(query_embedding)) \
            .limit(k_per_type) \
            .all()
        retrieved_context["settings"] = relevant_settings
        print(f"Retrieved {len(relevant_settings)} relevant settings.")
    except Exception as e:
        print(f"Error retrieving settings: {e}")

    # # 3. 检索相关过往场景概要 (核心上下文)
    try:
        scene_query = db.query(Scene) \
            .filter(
            Scene.project_id == project_id,
            Scene.summary_embedding != None,  # 必须有概要向量
            Scene.status.in_(['DRAFTED', 'REVISING', 'COMPLETED'])  # 只检索有内容的场景
        )
        # 如果提供了当前场景 ID，则排除它
        if current_scene_id is not None:
            scene_query = scene_query.filter(Scene.id != current_scene_id)

        relevant_past_scenes = scene_query \
            .order_by(Scene.summary_embedding.cosine_distance(query_embedding)) \
            .limit(k_per_type) \
            .all()
        retrieved_context["past_scenes"] = relevant_past_scenes
        print(f"Retrieved {len(relevant_past_scenes)} relevant past scenes.")
    except Exception as e:
        print(f"Error retrieving past scenes: {e}")

    # 4. 检索相关人物关系
    try:
        relevant_relationships = db.query(CharacterRelationship) \
            .filter(CharacterRelationship.project_id == project_id, CharacterRelationship.embedding != None) \
            .order_by(CharacterRelationship.embedding.cosine_distance(query_embedding)) \
            .limit(k_per_type) \
            .all()
        # 为了方便格式化，加载关联的角色名字
        for rel in relevant_relationships:
            db.refresh(rel, ['character1', 'character2'])  # 确保关联对象加载
        retrieved_context["character_relationships"] = relevant_relationships
        print(f"Retrieved {len(relevant_relationships)} relevant character relationships.")
    except Exception as e:
        print(f"Error retrieving character relationships: {e}")

    # 5. (可选) 检索相关章节概要 (提供宏观上下文)
    try:
        relevant_chapters = db.query(Chapter) \
            .filter(Chapter.project_id == project_id, Chapter.embedding != None) \
            .order_by(Chapter.embedding.cosine_distance(query_embedding)) \
            .limit(k_per_type // 2 or 1) \
            .all()
        retrieved_context["chapters"] = relevant_chapters
        print(f"Retrieved {len(relevant_chapters)} relevant chapters.")
    except Exception as e:
        print(f"Error retrieving chapters: {e}")

    print("Context retrieval finished.")
    return retrieved_context


# --- 格式化函数 ---

def format_context_for_prompt(
        retrieved_data: Dict[str, List[Any]],
        max_context_length: int = 2000  # 限制总上下文长度，防止超出 Token 限制
) -> str:
    """
    将检索到的数据格式化为适合放入 LLM Prompt 的文本字符串。

    Args:
        retrieved_data: `retrieve_relevant_context` 返回的字典。
        max_context_length: 格式化后上下文字符串的最大近似长度。

    Returns:
        一个包含所有相关上下文信息的格式化字符串。
    """
    context_parts = []
    current_length = 0

    # 定义各部分处理函数，方便管理和截断
    def format_characters(chars: List[Character]) -> str:
        nonlocal current_length
        part = "\n[Relevant Characters]:\n"
        added_len = len(part)
        if current_length + added_len > max_context_length: return ""
        current_length += added_len

        for char in chars:
            entry = f"- Name: {char.name}\n"
            if char.description: entry += f"  Description: {char.description[:200].strip()}...\n"
            if char.current_status: entry += f"  Current Status: {char.current_status.strip()}\n"
            if char.goals: entry += f"  Goals: {char.goals[:150].strip()}...\n"

            if current_length + len(entry) <= max_context_length:
                part += entry
                current_length += len(entry)
            else:
                part += "- (More characters truncated due to length limit)\n"
                current_length = max_context_length  # Mark as full
                break
        return part

    def format_settings(settings: List[SettingElement]) -> str:
        nonlocal current_length
        part = "\n[Relevant Settings/Lore]:\n"
        added_len = len(part)
        if current_length + added_len > max_context_length: return ""
        current_length += added_len

        for setting in settings:
            entry = f"- Name: {setting.name} ({setting.element_type})\n"
            if setting.description: entry += f"  Description: {setting.description[:250].strip()}...\n"

            if current_length + len(entry) <= max_context_length:
                part += entry
                current_length += len(entry)
            else:
                part += "- (More settings truncated due to length limit)\n"
                current_length = max_context_length
                break
        return part

    def format_past_scenes(scenes: List[Scene]) -> str:
        nonlocal current_length
        part = "\n[Relevant Past Scene Summaries (Most Recent First)]:\n"
        added_len = len(part)
        if current_length + added_len > max_context_length: return ""
        current_length += added_len

        # 按更新时间或创建时间倒序排列，给 LLM 最近的上下文
        sorted_scenes = sorted(
            scenes,
            key=lambda s: s.updated_at or s.created_at or func.now(),  # Fallback if None
            reverse=True
        )

        for scene in sorted_scenes:
            chapter_info = f"Chapter {scene.chapter.order}" if scene.chapter else "Unassigned Chapter"
            entry = f"- Scene ({chapter_info}, Order {scene.order_in_chapter}): {scene.title or 'Untitled Scene'}\n"
            if scene.summary:
                entry += f"  Summary: {scene.summary[:300].strip()}...\n"  # 使用概要比全文更节省空间
            elif scene.goal:
                entry += f"  Goal: {scene.goal[:200].strip()}...\n"  # Fallback to goal if no summary

            if current_length + len(entry) <= max_context_length:
                part += entry
                current_length += len(entry)
            else:
                part += "- (More past scenes truncated due to length limit)\n"
                current_length = max_context_length
                break
        return part

    def format_relationships(relationships: List[CharacterRelationship]) -> str:
        nonlocal current_length
        part = "\n[Relevant Character Relationships]:\n"
        added_len = len(part)
        if current_length + added_len > max_context_length: return ""
        current_length += added_len

        for rel in relationships:
            # 确保 character1 和 character2 已加载
            char1_name = rel.character1.name if rel.character1 else "Unknown"
            char2_name = rel.character2.name if rel.character2 else "Unknown"
            entry = f"- Relationship between {char1_name} and {char2_name}:\n"
            entry += f"  Type: {rel.relationship_type}\n"
            if rel.description: entry += f"  Details: {rel.description[:200].strip()}...\n"

            if current_length + len(entry) <= max_context_length:
                part += entry
                current_length += len(entry)
            else:
                part += "- (More relationships truncated due to length limit)\n"
                current_length = max_context_length
                break
        return part

    def format_chapters(chapters: List[Chapter]) -> str:
        nonlocal current_length
        part = "\n[Relevant Chapter Summaries]:\n"
        added_len = len(part)
        if current_length + added_len > max_context_length: return ""
        current_length += added_len

        for chapter in chapters:
            entry = f"- Chapter {chapter.order}: {chapter.title}\n"
            if chapter.summary: entry += f"  Summary: {chapter.summary[:300].strip()}...\n"

            if current_length + len(entry) <= max_context_length:
                part += entry
                current_length += len(entry)
            else:
                part += "- (More chapters truncated due to length limit)\n"
                current_length = max_context_length
                break
        return part

    # 按优先级添加上下文，重要的放前面
    if retrieved_data.get("characters"):
        context_parts.append(format_characters(retrieved_data["characters"]))
        if current_length >= max_context_length: return "".join(context_parts)

    if retrieved_data.get("settings"):
        context_parts.append(format_settings(retrieved_data["settings"]))
        if current_length >= max_context_length: return "".join(context_parts)

    if retrieved_data.get("character_relationships"):
        context_parts.append(format_relationships(retrieved_data["character_relationships"]))
        if current_length >= max_context_length: return "".join(context_parts)

    if retrieved_data.get("past_scenes"):
        context_parts.append(format_past_scenes(retrieved_data["past_scenes"]))
        if current_length >= max_context_length: return "".join(context_parts)

    if retrieved_data.get("chapters"):
        context_parts.append(format_chapters(retrieved_data["chapters"]))
        # No need to check length after the last part

    final_context = "".join(filter(None, context_parts))  # Filter out empty strings if truncated early

    if not final_context.strip():  # Handle case where nothing could be added
        return "[No relevant context found or context exceeds length limit]"

    # 添加总的包围结构
    return f"--- Relevant Context ---\n{final_context.strip()}\n--- End of Context ---"


# --- Core RAG Service Function ---
async def generate_scene_content_rag(
        db: Session,
        scene_id: int
) -> Scene:
    """
    Generates content for a specific scene using RAG.
    1. Fetches scene goal.
    2. Generates embedding for the goal.
    3. Retrieves relevant context using vector search.
    4. Formats context and goal into a prompt.
    5. Calls LLM to generate content.
    6. Updates scene with generated content, status, and optional summary/embedding.
    """
    # 1. Fetch the Scene
    scene = scene_service.get_scene(db, scene_id=scene_id)

    if not scene:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Scene with id {scene_id} not found.")
    if not scene.project_id:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Scene {scene_id} is missing project association.")

    if not scene.goal:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Scene {scene_id} has no goal defined. Cannot generate content.")

    print(f"Starting RAG generation for Scene ID: {scene_id}, Goal: '{scene.goal[:100]}...'")

    try:
        # 2. Get Query Embedding (Generate fresh embedding for the current goal)
        print("Generating embedding for scene goal...")
        query_embedding = await llm_service.get_embedding(scene.goal)

        # 3. Retrieve Relevant Context
        print("Retrieving relevant context...")
        retrieved_context = await retrieve_relevant_context(db, scene.project_id, query_embedding, 10,current_scene_id=scene_id)
        # print(f"Retrieved Context: {retrieved_context}") # DEBUG

        # 4. Format Context
        context_string = format_context_for_prompt(retrieved_context)
        print("Formatted Context String (truncated):")
        print(context_string[:500] + "..." if len(context_string) > 500 else context_string)

        # 5. Build Prompt
        # Prompt Engineering is key here! This is a basic example.
        prompt = f"""You are an AI assistant helping write a novel scene.
Generate the prose content for a scene based *only* on the provided Scene Goal and Relevant Context.
Focus on fulfilling the Scene Goal. Use the context to inform character actions, dialogue, setting details, and relationships.
Do not invent major characters or plot points not mentioned in the goal or context unless implied.
Write in a clear, engaging narrative style. Output only the scene content itself.

--- Relevant Context ---
{context_string}
--- End of Context ---

--- Scene Goal ---
{scene.goal}
--- End of Goal ---

Scene Content:
"""
        print("\n--- Generated Prompt (truncated) ---")  # DEBUG
        print(prompt[:1000] + "..." if len(prompt) > 1000 else prompt)  # DEBUG
        print("--- End of Prompt ---\n")  # DEBUG

        # 6. Call LLM to Generate Content
        print("Calling LLM for scene content generation...")
        generated_text = await llm_service.generate_text(prompt, max_tokens=3000)  # Adjust max_tokens as needed
        print("LLM generation complete.")
        print("\n--- Generated Content (truncated) ---")  # DEBUG
        print(generated_text[:500] + "..." if len(generated_text) > 500 else generated_text)  # DEBUG
        print("--- End of Generated Content ---\n")  # DEBUG

        # 7. Update Scene in Database
        scene_update = SceneUpdateGenerated(generated_content=generated_text, status=SceneStatus.DRAFTED)

        # 8. (Optional but Recommended) Generate Summary and Embedding for the generated content
        print("Generating summary for the new content...")
        try:
            summary = await llm_service.summarize_text(generated_text, max_tokens=300)
            scene_update.summary = summary
            print(f"Generated Summary: {summary[:200]}...")
            if summary:
                print("Generating embedding for the summary...")
                summary_embedding = await llm_service.get_embedding(summary)
                scene_update.summary_embedding = summary_embedding
                print("Summary embedding generated.")
            else:
                scene_update.summary_embedding = None
        except Exception as summary_err:
            # Don't fail the whole process if summarization fails, just log it
            print(f"Warning: Failed to generate summary or embedding for scene {scene_id}: {summary_err}")
            scene_update.summary = None  # Ensure summary is cleared if generation failed
            scene_update.summary_embedding = None

        await scene_service.update_scene_generated(db, scene_id=scene_id, scene_update=scene_update)

        print(f"Successfully generated content and updated Scene ID: {scene_id}")
        return scene

    except HTTPException as http_exc:
        raise http_exc  # Re-raise HTTP exceptions from LLM service or validation
    except Exception as e:
        print(f"Error during RAG generation for scene {scene_id}: {e}")
        import traceback
        traceback.print_exc()  # Log the full traceback for debugging
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred during scene generation: {e}"
        )
