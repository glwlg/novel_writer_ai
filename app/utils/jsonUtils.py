import json
import re


def extract_json_from_response(response: str) -> str:
    """
    从可能包含Markdown代码块的LLM响应中提取JSON字符串。

    Args:
        response: LLM返回的原始字符串。

    Returns:
        提取出的JSON字符串，如果找不到则返回原始字符串（可能导致后续解析失败）。
    """
    response = response.strip() # 去除首尾空白

    # 1. 尝试用正则表达式查找被 ```json ... ``` 或 ``` ... ``` 包裹的内容
    # re.DOTALL 让 . 匹配包括换行符在内的任何字符
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", response, re.DOTALL)
    if match:
        # 提取匹配到的第一个分组（括号里的内容）
        potential_json = match.group(1).strip()
        # 做一个基本检查，看它是否像JSON（以 [ 或 { 开头）
        if potential_json.startswith(('[', '{')) and potential_json.endswith((']', '}')):
             return potential_json # 返回提取并清理后的内容

    # 2. 如果没有找到Markdown块，或者提取内容不像JSON，
    #    检查整个响应（去除首尾空白后）是否直接是JSON
    if response.startswith(('[', '{')) and response.endswith((']', '}')):
        return response

    # 3. （可选，更宽松的尝试）查找第一个 '[' 或 '{' 和最后一个 ']' 或 '}'
    #    这可能不准确，但可以尝试挽救一些格式不太规整的情况
    start_chars = ['[', '{']
    end_chars = [']', '}']
    start_index = -1
    end_index = -1

    for char in start_chars:
        idx = response.find(char)
        if idx != -1:
            if start_index == -1 or idx < start_index:
                start_index = idx
            break # 通常JSON以 [ 或 { 中的一个开始

    for char in end_chars:
        idx = response.rfind(char)
        if idx != -1:
             if end_index == -1 or idx > end_index:
                 end_index = idx + 1 # rfind返回的是最后一个字符的索引，切片需要+1

    if start_index != -1 and end_index != -1 and start_index < end_index:
         potential_json = response[start_index:end_index].strip()
         # 再次检查基本结构
         if potential_json.startswith(('[', '{')) and potential_json.endswith((']', '}')):
             # 可以尝试解析一下，看是否真的是JSON
             try:
                 json.loads(potential_json)
                 return potential_json # 如果能解析，就返回它
             except json.JSONDecodeError:
                 pass # 解析失败，继续往下走

    # 4. 如果以上方法都失败，返回原始（清理过的）字符串，
    #    让调用者处理后续的解析错误，或者你可以选择在这里抛出异常
    print("警告：未能从响应中可靠地提取出JSON内容。将尝试直接解析原始响应。")
    return response