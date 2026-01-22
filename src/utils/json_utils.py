"""
JSON 工具函数

提供 JSON 提取和验证功能,用于处理 LLM 返回的文本
"""

import json
import re
from typing import Type, TypeVar
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


def extract_json_from_text(text: str) -> str:
    """
    从 LLM 返回的文本中提取 JSON 字符串
    
    支持处理:
    - ```json ... ``` markdown 标记
    - 前后废话文本
    - 多余的空白字符
    
    Args:
        text: LLM 返回的原始文本
    
    Returns:
        提取出的纯 JSON 字符串
    
    Raises:
        ValueError: 无法提取有效的 JSON
    """
    # 1. 尝试直接解析（LLM 很听话，只回了 JSON）
    try:
        json.loads(text)
        return text
    except json.JSONDecodeError:
        pass

    # 2. 移除 markdown 代码块标记
    # 匹配 ```json ... ``` 或 ``` ... ```
    code_block_pattern = r"```(?:json)?\s*([\s\S]*?)\s*```"
    code_match = re.search(code_block_pattern, text)
    if code_match:
        potential_json = code_match.group(1).strip()
        try:
            json.loads(potential_json)
            return potential_json
        except json.JSONDecodeError:
            pass
    
    # 3. 正则提取最外层的 {} 或 []
    # 匹配 JSON 对象
    object_pattern = r"\{[\s\S]*\}"
    obj_match = re.search(object_pattern, text)
    if obj_match:
        json_str = obj_match.group(0)
        try:
            # 二次验证是否合法
            json.loads(json_str)
            return json_str
        except json.JSONDecodeError:
            pass
    
    # 匹配 JSON 数组
    array_pattern = r"\[[\s\S]*\]"
    arr_match = re.search(array_pattern, text)
    if arr_match:
        json_str = arr_match.group(0)
        try:
            json.loads(json_str)
            return json_str
        except json.JSONDecodeError:
            pass
            
    # 4. 极端情况：尝试清理后再解析
    # 移除前后的非 JSON 字符
    cleaned = text.strip()
    # 找到第一个 { 或 [
    start_idx = -1
    for i, char in enumerate(cleaned):
        if char in ['{', '[']:
            start_idx = i
            break
    
    if start_idx >= 0:
        # 找到最后一个 } 或 ]
        end_idx = -1
        for i in range(len(cleaned) - 1, -1, -1):
            if cleaned[i] in ['}', ']']:
                end_idx = i
                break
        
        if end_idx > start_idx:
            potential_json = cleaned[start_idx:end_idx + 1]
            try:
                json.loads(potential_json)
                return potential_json
            except json.JSONDecodeError:
                pass
    
    # 5. 所有方法都失败
    raise ValueError(f"Could not extract valid JSON from text. First 200 chars: {text[:200]}...")


def validate_json_schema(json_str: str, model: Type[T]) -> T:
    """
    验证 JSON 字符串是否符合 Pydantic 模型
    
    Args:
        json_str: JSON 字符串
        model: Pydantic 模型类
    
    Returns:
        验证后的模型实例
    
    Raises:
        ValidationError: JSON 不符合 schema
    """
    return model.model_validate_json(json_str)
