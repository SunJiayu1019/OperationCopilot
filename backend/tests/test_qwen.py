from app.services.qwen import QwenAdapter
from app.services.errors import ModelOutputError


class FakeCompletions:
    def create(self, **kwargs):
        assert kwargs["model"] == "qwen-test"
        assert kwargs["response_format"] == {"type": "json_object"}
        return type("Response", (), {"choices": [type("Choice", (), {"message": type("Message", (), {"content": '{"summary":"可验证卖点"}'})()})()]})()


class FakeClient:
    def __init__(self):
        self.chat = type("Chat", (), {"completions": FakeCompletions()})()


def test_qwen_adapter_returns_json_from_compatible_client():
    adapter = QwenAdapter(client=FakeClient(), model="qwen-test")

    result = adapter.complete_json("总结商品", "商品资料")

    assert result == {"summary": "可验证卖点"}


def test_qwen_adapter_requires_api_key_when_client_not_injected(monkeypatch):
    monkeypatch.delenv("DASHSCOPE_API_KEY", raising=False)

    try:
        QwenAdapter()
    except RuntimeError as error:
        assert "DASHSCOPE_API_KEY" in str(error)
    else:
        raise AssertionError("expected missing API key error")


def test_qwen_rejects_non_json_response():
    adapter = QwenAdapter(client=FakeClient(), model="qwen-test")
    adapter.client.chat.completions.create = lambda **kwargs: type("Response", (), {"choices": [type("Choice", (), {"message": type("Message", (), {"content": "not json"})()})()]})()

    try:
        adapter.complete_json("system", "user")
    except ModelOutputError:
        pass
    else:
        raise AssertionError("expected invalid model output error")


def test_qwen_rejects_wrong_task_shape():
    adapter = QwenAdapter(client=FakeClient(), model="qwen-test")
    try:
        adapter.generate_copy("海盐坚果脆", "品牌规范")
    except ModelOutputError:
        pass
    else:
        raise AssertionError("expected missing copy_variants error")
