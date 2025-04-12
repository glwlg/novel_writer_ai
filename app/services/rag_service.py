# 在你的 RAG 服务函数内部
import json

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.models import Character, CharacterRelationship, SettingElement, Scene, Chapter
from sqlalchemy.orm import Session, selectinload
from typing import List, Dict, Any, Optional

from app.models.structure import SceneStatus
from app.schemas import SceneUpdate, ChapterUpdate
from app.schemas.scene import SceneUpdateGenerated, SceneCreate
from app.services import llm_service, scene_service, chapter_service
from app.utils import jsonUtils


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


async def generate_scenes(
        db: Session,
        chapter_id: int
) -> Chapter:
    system_prompt = """
# 提示词：生成小说章节场景列表 (JSON格式)
你是一位经验丰富的小说编辑和创意助手。你的任务是根据提供的<小说概要>、<相关背景>和<章节信息>，为一个特定的小说章节构思并生成一系列场景（大约3-4个）。
请将结果以严格的JSON格式返回，该JSON是一个包含多个场景对象的数组，每个对象包含“title”和“goal”两个键。

**任务要求:**

1.  **分析输入信息：** 仔细阅读小说概要、相关背景和章节信息，理解本章节在整个故事结构中的功能和需要达成的叙事目的。
2.  **构思场景：** 将章节内容合理地分解为 **3到4个** 逻辑连贯或有递进关系的场景。每个场景应聚焦于一个具体的事件、对话、行动或情绪/信息节点。
3.  **定义场景目标：** 为每个场景明确其核心目的或需要展现的核心内容。这应该简洁地说明该场景要达成什么效果，例如：
    *   引入新角色或关键信息
    *   展现人物的内心挣扎或决策过程
    *   推动情节发展，制造转折点
    *   加剧或缓和某个冲突
    *   建立或破坏人物关系
    *   营造特定的氛围或悬念
    *   为后续情节埋下伏笔
4.  **生成JSON输出：** 严格按照以下JSON格式组织结果。确保输出是纯粹的JSON代码块，不包含任何额外的解释性文字或代码块标记符之外的内容。

```json
[
  {
    "title": "（为第一个场景取的简洁标题）",
    "goal": "（描述第一个场景的核心目标/主要内容/要达成的效果）"
  },
  {
    "title": "（为第二个场景取的简洁标题）",
    "goal": "（描述第二个场景的核心目标/主要内容/要达成的效果）"
  },
  {
    "title": "（为第三个场景取的简洁标题）",
    "goal": "（描述第三个场景的核心目标/主要内容/要达成的效果）"
  }
  // 如果有第四个场景，请继续添加
  // {
  //   "title": "（为第四个场景取的简洁标题）",
  //   "goal": "（描述第四个场景的核心目标/主要内容/要达成的效果）"
  // }
]
```

**请严格遵守：**

*   场景的目标不能超过<章节信息>中的内容；<相关背景>是作为信息参考方便你理解<章节信息>中的内容。
*   输出**必须**是格式完全正确的JSON数组，直接可供Python等程序解析。
*   JSON中只包含指定的`title`和`goal`两个字段。
*   场景数量控制在3或4个。
*   场景目标描述应精炼、准确，点明核心。
*   场景的划分和目标设定应紧密围绕<章节信息>所指示的主题或事件。
```
            """

    # 1. Fetch the Scene
    chapter = chapter_service.get_chapter(db, chapter_id=chapter_id)

    if not chapter:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Chapter with id {chapter_id} not found.")
    if not chapter.project_id:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Chapter {chapter_id} is missing project association.")

    try:
        # 2. Get Query Embedding (Generate fresh embedding for the current goal)
        print("Generating embedding for chapter title...")
        query_embedding = await llm_service.get_embedding(chapter.title)

        # 3. Retrieve Relevant Context
        print("Retrieving relevant context...")
        # 如果不是第一个章节，需要获取上一个章节的上下文
        current_chapter_id = None
        if chapter.order != 0:
            current_chapter_id = chapter_id
        retrieved_context = await retrieve_relevant_context(db, chapter.project_id, query_embedding, 10,
                                                            current_chapter_id=current_chapter_id)
        # print(f"Retrieved Context: {retrieved_context}") # DEBUG

        # 4. Format Context
        context_string = format_context_for_prompt(retrieved_context, max_context_length=20000)
        print("Formatted Context String (truncated):")
        print(context_string[:500] + "..." if len(context_string) > 500 else context_string)

        chapter_info = f"第 {chapter.order + 1} 章: {chapter.title}"

        # 5. Build Prompt
        # Prompt Engineering is key here! This is a basic example.
        prompt = f"""
<小说概要>
标题：{chapter.project.title}
风格：{chapter.project.style}
概要：
{chapter.project.logline}
</小说概要>
<章节信息>
第 {chapter.order + 1} 章: {chapter.title}
章节概要：
{chapter.summary}
</章节信息>
<相关背景>
{context_string}
</相关背景>
"""
        print("\n--- Generated Prompt (truncated) ---")  # DEBUG
        print(prompt)  # DEBUG
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

        try:
            json_string_to_parse = jsonUtils.extract_json_from_response(generated_text)
            print("--- 提取出的待解析字符串 ---")
            print(json_string_to_parse)
            print("---------------------------\n")
            scene_list = json.loads(json_string_to_parse)
            for i, scene in enumerate(scene_list):
                print(f"--- 场景 {i + 1} ---")
                print(f"标题: {scene.get('title')}")
                print(f"目标: {scene.get('goal')}")
                scene_create = SceneCreate(
                    project_id=chapter.project_id,
                    chapter_id=chapter_id,
                    title=scene.get('title'),
                    goal=scene.get('goal'),
                    status=SceneStatus.PLANNED,
                    order_in_chapter=i
                )
                await scene_service.create_scene(db, scene=scene_create)

        except json.JSONDecodeError as e:
            print(f"JSON解析错误: {e}")
            print(f"原始响应: {generated_text}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to parse LLM response as JSON: {e}"
            )


        print(f"Successfully generated scenes for : {chapter.title}")
        return chapter

    except HTTPException as http_exc:
        raise http_exc  # Re-raise HTTP exceptions from LLM service or validation
    except Exception as e:
        print(f"Error during generation scenes for chapter {chapter_id}: {e}")
        import traceback
        traceback.print_exc()  # Log the full traceback for debugging
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred during generation scenes : {e}"
        )


async def generate_scene_content(
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
你是一名AI小说写作助手。你的任务是根据下面给出的<小说概要>、<相关背景>和<场景目标>，撰写相应的场景内容。
请注意：
创作时必须完全基于所提供的<小说概要>、<相关背景>和<场景目标>。
写作的中心是实现<场景目标>。
请运用<相关背景>来设计人物的行为、对话、场景细节以及他们之间的关系。
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
标题：{scene.chapter.volume.project.title}
风格：{scene.chapter.volume.project.style}
概要：
{scene.chapter.volume.project.logline}
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
**小说章节创作指令：整合、深化与扩写**

**核心任务：** 请将下方按顺序提供的多个文本片段，**无缝整合**并进行**深度扩写**，创作出一个**逻辑连贯、情节饱满、细节丰富、引人入胜**的单一小说章节。

**具体要求：**

1.  **整合与流畅性 (Integration & Flow):**
    *   **无缝衔接：** 必须将所有片段自然地融合成一个有机的整体。运用必要的过渡性描写（场景转换、时间流逝暗示等）和内心活动（承上启下的思考、情绪转变等），确保片段间的逻辑链条清晰、转换顺滑，没有任何生硬的跳跃感。
    *   **叙事连贯：** 保持统一的叙事视角（除非片段本身包含视角转换且需要保留）。确保人物状态、情绪发展和情节推进具有内在的一致性和逻辑性。

2.  **深度扩写与丰富化 (Expansion & Enrichment):**
    *   **目标篇幅：** 在保持核心内容不变的前提下，将总字数扩充至 **[8000字]** 左右。扩写需**有意义、有价值**，而非简单重复或填充。
    *   **感官沉浸 (Sensory Immersion):** 大幅增加**具体、生动**的感官细节。不仅限于视觉，要充分调动听觉、嗅觉、触觉、味觉（若适用）的描写，让读者仿佛身临其境。
    *   **环境互动 (Environmental Interaction):** 细化环境描写，不仅仅是静态呈现，更要描写角色与环境的互动，环境如何影响角色的情绪、决策和行动。
    *   **人物内心深掘 (Character Depth):** 极大地丰富角色的内心世界。详细描绘其**即时**的心理活动、情绪波动（从细微到剧烈）、内在冲突、动机分析、价值判断、即时回忆闪现（与当前情境相关的）、潜意识的想法等。让人物行为有充分的心理依据支撑。
    *   **行动过程细化 (Action Detailing):** 将关键动作、行为或过程进行分解，描写具体的步骤、姿态、力度、微表情等，增强画面感和真实感。
    *   **对话与潜台词 (Dialogue & Subtext):** 如果片段包含对话，可适当扩充对话内容，使其更自然、更符合人物性格，并可能包含未言明的潜台词或暗示。补充对话间的神态、动作和心理反应。
    *   **氛围营造 (Atmosphere Building):** 根据情节需要，运用恰当的语言风格、节奏控制、环境烘托和心理描写，**精准地**营造和强化所需的情绪氛围（如紧张、悬疑、温馨、悲怆、压抑、神秘等）。
    *   **张力构建 (Tension & Pacing):** 在冲突点、关键转折或高潮部分，**有意识地控制叙事节奏**。可通过增加细节、放慢动作描写、强化心理博弈、运用悬念等手法，逐步积累并释放戏剧张力。

3.  **核心剧情的绝对忠诚 (Plot Fidelity):**
    *   **严守核心：** **绝对禁止**修改或偏离原始片段提供的**核心情节事件、关键设定、人物关系、事件的起因和结果**。扩写是在此基础上丰富血肉，绝非改动骨架。
    *   **避免画蛇添足：** 新增内容必须服务于原有情节、人物或氛围，不得引入与核心剧情无关或可能导致逻辑矛盾的新元素。

4.  **文风与表达 (Style & Expression):**
    *   **生动有力：** 追求**精准、生动、富有表现力**的语言。避免过度使用空洞的形容词和副词，力求用具体的描写展现效果。
    *   **叙事节奏：** 根据内容需要，灵活调整叙事节奏，快慢结合，张弛有度。
    *   **沉浸体验：** 最终目标是创作出能让读者**深度沉浸、情感共鸣、阅读体验流畅愉悦** (“读得爽”) 的章节。

5.  **输出要求 (Output Format):**
    *   **纯净正文：** **请严格只输出最终整合扩写后的小说章节正文。**
    *   **无附加信息：** 不要包含任何解释性文字、操作说明、分析、标记（如【扩写部分】）或任何非小说正文的内容。
    *   **纯文本格式：** 不要包含任何markdown语法标记。
    *   **语言：** 不要出现任何英文内容。
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
