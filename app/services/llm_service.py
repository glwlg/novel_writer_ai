# backend/app/services/llm_service.py

from typing import List, Optional

from openai import OpenAI
from app.core.config import settings

client = OpenAI(api_key=settings.OPENAI_API_KEY, base_url=settings.OPENAI_API_BASE)


# 文本流生成
async def generate_text_stream(messages, max_tokens: int = 150) -> str:
    messages_data = [{'role': message['role'], 'content': message['content']} for message in messages]
    try:
        response = client.chat.completions.create(model=settings.OPENAI_MODEL,
                                                  messages=messages_data,
                                                  max_tokens=max_tokens,
                                                  stream=True,
                                                  temperature=0.7)
        response_str = ''
        for part in response:
            if len(part.choices) == 0:
                continue
            choice = part.choices[0]
            if choice.finish_reason == 'stop':
                break
            # error handling
            if choice.finish_reason == 'length':
                break
            delta = choice.delta
            if delta == {} or delta.content is None:
                char = ''
            else:
                char = delta.content
            print(char)
            response_str += char
        return response_str
    except Exception as e:
        print(f"Error calling OpenAI API: {e}")
        # 更健壮的错误处理
        return f"Error generating text: {e}"


async def generate_text(prompt: str, max_tokens: int = 150) -> str:
    messages = [
        {"role": "system", "content": "You are a helpful assistant writing a novel."},
        {"role": "user", "content": prompt}
    ]
    return await generate_text_stream(messages, max_tokens=max_tokens)


async def summarize_text(prompt: str, max_tokens: int = 150) -> str:
    messages = [
        {"role": "system",
         "content": "You are a helpful assistant writing a novel.please summarize the following text"},
        {"role": "user", "content": prompt}
    ]
    return await generate_text_stream(messages, max_tokens=max_tokens)


# 未来可以添加获取 embedding 的函数等
async def get_embedding(text: str) -> List[float]:
    response = client.embeddings.create(
        model="text-embedding-v3",  # 或其他嵌入模型
        input=text,
        dimensions=1024,
        encoding_format="float"
    )
    return response.data[0].embedding


def prepare_text_for_embedding(*args: Optional[str]) -> str:
    """将多个可能为 None 的字符串字段安全地连接成一个用于嵌入的文本块。"""
    return " ".join(filter(None, args)).strip()


def create_augmented_prompt(scene_goal: str, context_str: str, additional_instructions: str = "") -> str:
    """构建最终用于 LLM 的 Prompt"""

    prompt = f"""You are a novelist writing a scene for a story. Your task is to write the content for the following scene goal:

    [Scene Goal]:
    {scene_goal}

    Please use the following context information retrieved from the story's knowledge base to ensure consistency and relevance. Do not simply repeat the context, but use it to inform your writing.

    {context_str}

    [Additional Instructions]:
    {additional_instructions if additional_instructions else "Write the scene in a compelling and engaging style. Focus on showing, not telling."}

    Now, write the scene content:
    """
    return prompt
