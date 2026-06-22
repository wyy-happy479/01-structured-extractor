"""
核心抽取器：API 调用 → JSON 解析 → Pydantic 校验 → 失败重试。

重试策略：当解析或校验失败时，将错误信息追加到对话中，
让模型看到"自己上一轮输出了什么 + 哪里错了"，从而自我修正。
"""
import json
import os
from openai import OpenAI
from pydantic import ValidationError

from schemas import SCHEMA_MAP
from prompts import PROMPT_MAP

MAX_RETRIES = 3

# 每种类型的字段修正提示（只在 model_validate 失败时用）
RETRY_HINTS = {
    "resume": (
        "- 所有 `*_confidence` 字段是 number 类型，取值范围 0.0 ~ 1.0\n"
        "- skills 和 project_names、project_descriptions 是数组类型（即使只有一个元素也要用 [] 包起来）\n"
        "- years_of_experience 是 number 或 null，不要填字符串"
    ),
    "contract": (
        "- 所有 `*_confidence` 字段是 number 类型，取值范围 0.0 ~ 1.0\n"
        "- key_terms 是数组类型（即使只有一条也要用 [] 包起来）\n"
        "- amount 是 number 或 null，不要带「元」或逗号\n"
        "- start_date / end_date 为 YYYY-MM-DD 格式的字符串或空字符串"
    ),
    "product": (
        "- 所有 `*_confidence` 字段是 number 类型，取值范围 0.0 ~ 1.0\n"
        "- features 是数组类型（即使只有一个卖点也要用 [] 包起来）\n"
        "- specifications 是对象类型（key-value 对）\n"
        "- price 是 number 或 null，只填数字不要带「元」或货币符号"
    ),
}


class ExtractionError(Exception):
    """抽取失败异常（重试耗尽后仍失败时抛出）"""
    pass


def extract(text: str, extract_type: str, max_retries: int = MAX_RETRIES):
    """
    从文本中抽取结构化信息。

    流程：
    1. 根据 extract_type 选择对应的 Prompt 和 Schema
    2. 调用 DeepSeek API（JSON mode）
    3. 解析 JSON → Pydantic 校验
    4. 失败时把错误信息反馈给模型，重试（最多 max_retries 次）

    Args:
        text: 待抽取的原始文本
        extract_type: 抽取类型 — "resume" | "contract" | "product"
        max_retries: 最大重试次数

    Returns:
        校验通过的 Pydantic 模型实例

    Raises:
        ExtractionError: 所有重试耗尽后仍然失败
        ValueError: extract_type 不合法
    """
    if extract_type not in SCHEMA_MAP:
        raise ValueError(
            f"不支持的抽取类型: {extract_type}，"
            f"可选: {list(SCHEMA_MAP.keys())}"
        )

    schema_cls = SCHEMA_MAP[extract_type]
    system_prompt = PROMPT_MAP[extract_type]

    client = OpenAI(
        api_key=os.environ.get("DASHSCOPE_API_KEY"),
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    )

    # 对话消息列表：system prompt + 用户输入
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": text},
    ]

    last_error = None

    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model="qwen-max",
                messages=messages,
                response_format={"type": "json_object"},
                temperature=0.1,     # 低温度 → 输出更稳定、确定性更高
            )

            raw_output = response.choices[0].message.content

            # ── 第 1 关：JSON 解析 ──
            try:
                data = json.loads(raw_output)  # 返回一个字典，用于 LLM 调用
            except json.JSONDecodeError as e:
                last_error = f"JSON 解析失败: {e}"
                messages.append({"role": "assistant", "content": raw_output})
                messages.append({
                    "role": "user",
                    "content": (
                        f"你的输出无法解析为 JSON。错误: {e}\n"
                        f"请重新输出，确保是合法的 JSON 格式。"
                    ),
                })
                
                continue  # 重试

            # ── 第 2 关：Pydantic 校验 ──
            try:
                result = schema_cls.model_validate(data)
                return result  # ✅ 校验通过，返回结果
            except ValidationError as e:
                last_error = f"字段校验失败"
                hint = RETRY_HINTS.get(extract_type, "")
                messages.append({"role": "assistant", "content": raw_output})
                messages.append({
                    "role": "user",
                    "content": (
                        f"你的输出校验失败，以下是具体错误:\n{e}\n\n"
                        f"请修正后重新输出完整的 JSON。提示:\n{hint}"
                    ),
                })
                
                continue  # 重试

        except Exception as e:
            # API 调用层面的异常（网络、限流等）
            last_error = f"API 调用失败: {e}"
            if attempt < max_retries - 1:
                continue
            raise ExtractionError(
                f"重试 {max_retries} 次后仍然失败。最后错误: {last_error}"
            ) from e

    # 重试次数耗尽
    raise ExtractionError(
        f"重试 {max_retries} 次后仍然失败。最后错误: {last_error}"
    )
