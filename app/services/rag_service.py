# 在你的 RAG 服务函数内部
from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.models import Character, CharacterRelationship, SettingElement, Scene, Chapter
from sqlalchemy.orm import Session, selectinload
from typing import List, Dict, Any, Optional

from app.models.structure import SceneStatus
from app.schemas import SceneUpdate, ChapterUpdate
from app.schemas.scene import SceneUpdateGenerated
from app.services import llm_service, scene_service, chapter_service


# --- 检索函数 ---

async def retrieve_relevant_context(
        db: Session,
        project_id: int,
        query_embedding: List[float],
        k_per_type: int,  # 每个类别检索多少条
        current_chapter_id: Optional[int] = None,
        current_scene_id: Optional[int] = None,  # 用于排除正在生成的场景自身
) -> Dict[str, List[Any]]:
    """
    从数据库检索与查询向量相关的上下文信息。

    Args:
        project_id: 当前项目的 ID。
        query_embedding: 查询文本（如场景目标）的向量。
        k_per_type: 每个信息类别（角色、设定、场景等）最多检索的条数。
        db: SQLAlchemy 数据库会话。
        current_chapter_id: (可选) 当前正在处理的章节 ID。
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
        "last_chapter": [],
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

    if current_chapter_id is not None:
        # 5. 检索上一章节
        try:
            last_chapter = db.query(Chapter) \
                .filter(Chapter.project_id == project_id, Chapter.id < current_chapter_id) \
                .order_by(Chapter.order.desc()) \
                .first()
            retrieved_context["last_chapter"] = [last_chapter]
        except Exception as e:
            print(f"Error last_chapter: {e}")

    # 6. (可选) 检索相关章节概要 (提供宏观上下文)
    # try:
    #     relevant_chapters = db.query(Chapter) \
    #         .filter(Chapter.project_id == project_id, Chapter.embedding != None) \
    #         .order_by(Chapter.embedding.cosine_distance(query_embedding)) \
    #         .limit(k_per_type // 2 or 1) \
    #         .all()
    #     retrieved_context["chapters"] = relevant_chapters
    #     print(f"Retrieved {len(relevant_chapters)} relevant chapters.")
    # except Exception as e:
    #     print(f"Error retrieving chapters: {e}")

    print("Context retrieval finished.")
    return retrieved_context


# --- 格式化函数 ---

def format_context_for_prompt(
        retrieved_data: Dict[str, List[Any]],
        max_context_length: int = 20000  # 限制总上下文长度，防止超出 Token 限制
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
        part = "\n[相关角色]:\n"
        added_len = len(part)
        if current_length + added_len > max_context_length: return ""
        current_length += added_len

        for char in chars:
            entry = f"- 姓名: {char.name}\n"
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
        part = "\n[相关设定/概念]:\n"
        added_len = len(part)
        if current_length + added_len > max_context_length: return ""
        current_length += added_len

        for setting in settings:
            entry = f"- 名称: {setting.name} ({setting.element_type})\n"
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
        part = "\n[相关场景概要（相关度优先）]:\n"
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
            chapter_info = f"第 {scene.chapter.order + 1} 章" if scene.chapter else "未知章节"
            entry = f"- 场景 ({chapter_info}, 第 {scene.order_in_chapter + 1} 个场景): {scene.title or '未命名场景'}\n"
            if scene.summary:
                entry += f"  概要: {scene.summary[:1000].strip()}...\n"
            elif scene.goal:
                entry += f"  目标: {scene.goal[:500].strip()}...\n"

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
        part = "\n[相关角色关系]:\n"
        added_len = len(part)
        if current_length + added_len > max_context_length: return ""
        current_length += added_len

        for rel in relationships:
            # 确保 character1 和 character2 已加载
            char1_name = rel.character1.name if rel.character1 else "未知"
            char2_name = rel.character2.name if rel.character2 else "未知"
            entry = f"- {char1_name} 与 {char2_name} 之间的关系:\n"
            entry += f"  关系类型: {rel.relationship_type}\n"
            if rel.description: entry += f"  Details: {rel.description[:200].strip()}...\n"

            if current_length + len(entry) <= max_context_length:
                part += entry
                current_length += len(entry)
            else:
                part += "- (More relationships truncated due to length limit)\n"
                current_length = max_context_length
                break
        return part

    def format_last_chapter(chapters: List[Chapter]) -> str:
        nonlocal current_length
        if len(chapters) < 1:
            return ""
        chapter = chapters[0]
        if not chapter:
            return ""
        part = "\n[上个章节概要]:\n"
        added_len = len(part)
        if current_length + added_len > max_context_length: return ""
        current_length += added_len

        entry = f"- 第 {chapter.order + 1} 章: {chapter.title}\n"
        if chapter.summary: entry += f"  概要: {chapter.summary[:1000].strip()}...\n"

        if current_length + len(entry) <= max_context_length:
            part += entry
            current_length += len(entry)
        else:
            part += "- (更多章节受限长度被截断)\n"
            current_length = max_context_length
        return part

    def format_chapters(chapters: List[Chapter]) -> str:
        nonlocal current_length
        part = "\n[相关章节概要]:\n"
        added_len = len(part)
        if current_length + added_len > max_context_length: return ""
        current_length += added_len

        for chapter in chapters:
            entry = f"- 第 {chapter.order + 1} 章: {chapter.title}\n"
            if chapter.summary: entry += f"  概要: {chapter.summary[:1000].strip()}...\n"

            if current_length + len(entry) <= max_context_length:
                part += entry
                current_length += len(entry)
            else:
                part += "- (更多章节受限长度被截断)\n"
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

    if retrieved_data.get("last_chapter"):
        context_parts.append(format_last_chapter(retrieved_data["last_chapter"]))

    if retrieved_data.get("chapters"):
        context_parts.append(format_chapters(retrieved_data["chapters"]))
        # No need to check length after the last part

    final_context = "".join(filter(None, context_parts))  # Filter out empty strings if truncated early

    if not final_context.strip():  # Handle case where nothing could be added
        return "[No relevant context found or context exceeds length limit]"

    # 添加总的包围结构
    return f"<相关上下文>\n{final_context.strip()}\n</相关上下文>"


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
    system_prompt = """
你是一名AI小说写作助手。你的任务是根据下面给出的“场景目标”和“相关背景”，撰写相应的场景内容。
请注意：
创作时必须完全基于所提供的“场景目标”和“相关背景”。
写作的中心是实现“场景目标”。
请运用“相关背景”来设计人物的行为、对话、场景细节以及他们之间的关系。（重要：如果这是章节中的后续场景，请确保“相关背景”包含了前一场景结尾时的关键信息，如人物情绪、位置、遗留问题等。）
保持连贯性： 确保本场景的开端与“相关背景”中提供的前续场景信息（人物状态、情节进展、环境等）自然衔接，避免逻辑冲突或状态突变。
除非“目标”或“背景”中已有暗示，否则不要自行添加新的主要角色或重要故事情节。
请用清晰、有吸引力的叙事风格来写。
最后，只需输出场景本身的内容，不要附加任何说明或标签。
            """
    summarize_system_prompt = """
角色： AI内容摘要助手。
任务： 请仔细阅读下方提供的完整小说场景文本，并为其生成一份简洁的摘要。
摘要应涵盖：
场景发生的主要事件和流程概要。
核心的冲突或解决的问题。
角色之间最重要的互动或关系变化。
场景传递的关键信息或达成的主要目的。
要求：
摘要必须忠实于原文内容。
语言精练、清晰、高度概括。
旨在让人快速了解该场景的核心内容和作用。
输出： 仅提供该场景的摘要文字，通常是一小段话或几个关键句子。
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
        # 如果是章节中的第一个场景，需要查询上一章节
        current_chapter_id = None
        if scene.order_in_chapter == 0:
            current_chapter_id = scene.chapter_id
        retrieved_context = await retrieve_relevant_context(db, scene.project_id, query_embedding, 10,
                                                            current_chapter_id=current_chapter_id,
                                                            current_scene_id=scene_id)
        # print(f"Retrieved Context: {retrieved_context}") # DEBUG

        # 4. Format Context
        context_string = format_context_for_prompt(retrieved_context, max_context_length=20000)
        print("Formatted Context String (truncated):")
        print(context_string[:500] + "..." if len(context_string) > 500 else context_string)

        chapter_info = f"第 {scene.chapter.order + 1} 章" if scene.chapter else "未知章节"
        current_scene = f"- 场景 ({chapter_info}, 第 {scene.order_in_chapter + 1} 个场景): {scene.title or '未命名场景'}\n"

        # 5. Build Prompt
        # Prompt Engineering is key here! This is a basic example.
        prompt = f"""
<小说概要>
{scene.project.title}

{scene.project.logline}
</小说概要>
<相关背景>
{context_string}
</相关背景>
<场景目标>
请完成 {current_scene}
{scene.goal}
</场景目标>
"""
        print("\n--- Generated Prompt (truncated) ---")  # DEBUG
        print(prompt[:1000] + "..." if len(prompt) > 1000 else prompt)  # DEBUG
        print("--- End of Prompt ---\n")  # DEBUG

        # 6. Call LLM to Generate Content
        print("Calling LLM for scene content generation...")
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]
        generated_text = await llm_service.generate_text(messages, max_tokens=48000)
        print("LLM generation complete.")
        print("\n--- Generated Content (truncated) ---")  # DEBUG
        print(generated_text[:500] + "..." if len(generated_text) > 500 else generated_text)  # DEBUG
        print("--- End of Generated Content ---\n")  # DEBUG

        # 7. Update Scene in Database
        scene_update = SceneUpdateGenerated(generated_content=generated_text, status=SceneStatus.DRAFTED)

        # 8. (Optional but Recommended) Generate Summary and Embedding for the generated content
        print("Generating summary for the new content...")
        try:
            messages = [
                {"role": "system", "content": summarize_system_prompt},
                {"role": "user", "content": generated_text}
            ]
            summary = await llm_service.generate_text(messages, max_tokens=28000)
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


# --- Core RAG Service Function ---
async def generate_chapter_content(
        db: Session,
        chapter_id: int
) -> Chapter:

    system_prompt = """
# 小说章节整合与深度扩写任务
请将下方提供的几个文本片段，按照它们提供的顺序，整合并深度扩写成一个**连贯流畅、内容丰富**的单一章节。

**目标：**

1.  **整合与衔接：** 将所有提供的片段无缝融合，确保情节、时间、逻辑和人物状态的**自然过渡与连贯性**。补充必要的过渡性描写和心理活动，使得原本分离的片段读起来像一个有机的整体。
2.  **深度扩写：** 在**严格保持原有核心剧情事件和发展顺序不变**的前提下，对内容进行大幅度扩充，目标字数达到 **[8000字左右]**。扩写的重点在于：
    *   **丰富细节：** 增加环境描写的层次感、感官细节（视觉、听觉、嗅觉、触觉等）、动作描写的具体过程。
    *   **深化人物：** 深入挖掘角色的内心世界，补充其在各个场景下的心理活动、情绪变化、思考、回忆闪现、动机挣扎等。
    *   **强化氛围：** 根据不同片段的基调，着力渲染所需的情绪氛围（例如：紧张、悬疑、悲伤、激昂、宁静、压抑等）。
    *   **增强张力：** 对于冲突、关键转折或高潮部分，适当放慢节奏，增加铺垫和细节描写，提升戏剧张力。
3.  **避免冗余：** 扩写应追求**有意义的丰富**，而非简单的词语堆砌或情节重复。确保新增内容服务于情节推进、人物塑造或氛围营造。避免空洞的形容词滥用和无意义的拉长句子。
4.  **保持核心剧情：** **绝对不允许**修改原有片段中的关键情节、事件结果、核心设定或人物关系。扩写是在原有骨架上填充血肉，而不是改变骨架。
5.  **文风要求：** 整体文风需**引人入胜，富有表现力**。请根据各片段内容，自然调整叙事节奏和语言风格，力求让读者获得沉浸式的阅读体验（即“读得爽”）
6.  **输出格式：** **请严格仅输出最终整合扩写后的小说章节正文。** 不要包含任何关于你执行了哪些操作的说明、对提示词的分析、诸如【扩写部分】之类的标记，或任何非小说正文的内容。
            """


    # 1. Fetch the Chapter
    chapter = chapter_service.get_chapter(db, chapter_id=chapter_id)

    if not chapter:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Chapter with id {chapter_id} not found.")
    if not chapter.project_id:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Chapter {chapter_id} is missing project association.")

    try:
        # 2. Build Prompt
        if not chapter.scenes:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail=f"Chapter {chapter_id} has no scenes defined. Cannot generate content.")

        prompt = ""
        for scene in chapter.scenes:
            if scene.generated_content:
                prompt += scene.generated_content + "\n"


        print("\n--- Generated Prompt (truncated) ---")  # DEBUG
        print(prompt[:1000] + "..." if len(prompt) > 1000 else prompt)  # DEBUG
        print("--- End of Prompt ---\n")  # DEBUG

        # 3. Call LLM to Generate Content
        print("Calling LLM for scene content generation...")
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]
        generated_text = await llm_service.generate_text(messages, max_tokens=48000)
        print("LLM generation complete.")
        print("\n--- Generated Content (truncated) ---")  # DEBUG
        print(generated_text[:500] + "..." if len(generated_text) > 500 else generated_text)  # DEBUG
        print("--- End of Generated Content ---\n")  # DEBUG

        # 4. Update Chapter in Database
        chapter_update = ChapterUpdate(content=generated_text)

        await chapter_service.update_chapter(db, db_chapter=chapter, chapter_in=chapter_update)

        print(f"Successfully generated content and updated Chapter ID: {chapter_id}")
        return chapter

    except HTTPException as http_exc:
        raise http_exc  # Re-raise HTTP exceptions from LLM service or validation
    except Exception as e:
        print(f"Error during RAG generation for chapter {chapter_id}: {e}")
        import traceback
        traceback.print_exc()  # Log the full traceback for debugging
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred during chapter generation: {e}"
        )
