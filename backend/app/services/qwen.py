import json
import os
from typing import Any
from pydantic import ValidationError

from .errors import ModelOutputError
from .prompts import PromptRegistry
from .schemas import CopyResult, ReviewResult, SummaryResult


class QwenAdapter:
    def __init__(self, client: Any | None = None, model: str | None = None) -> None:
        self.model = model or os.getenv("QWEN_MODEL", "qwen-plus")
        if client is not None:
            self.client = client
            return
        api_key = os.getenv("DASHSCOPE_API_KEY")
        if not api_key:
            raise RuntimeError("DASHSCOPE_API_KEY is required when Qwen client is not injected")
        from openai import OpenAI
        self.client = OpenAI(api_key=api_key, base_url=os.getenv("QWEN_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1"))

    def complete_json(self, system_prompt: str, user_prompt: str, temperature: float = 0.3) -> dict[str, Any]:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
            temperature=temperature,
            response_format={"type": "json_object"},
        )
        content = response.choices[0].message.content or ""
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError as error:
            raise ModelOutputError("Qwen returned invalid JSON") from error
        if not isinstance(parsed, dict):
            raise ModelOutputError("Qwen JSON output must be an object")
        return parsed

    def summarize(self, content: str, context: str = "") -> dict[str, Any]:
        return self._validated(SummaryResult, PromptRegistry.product_summary(), content, context)

    def generate_copy(self, content: str, context: str = "") -> dict[str, Any]:
        return self._validated(CopyResult, PromptRegistry.copy_generation(), content, context)

    def review_copy(self, content: str, context: str = "") -> dict[str, Any]:
        return self._validated(ReviewResult, PromptRegistry.content_review(), content, context)

    def _validated(self, schema: type, system_prompt: str, content: str, context: str) -> dict[str, Any]:
        result = self.complete_json(system_prompt, f"内容：{content}\n检索证据：{context}")
        try:
            return schema.model_validate(result).model_dump()
        except ValidationError as error:
            raise ModelOutputError(f"Qwen output does not match {schema.__name__}") from error
