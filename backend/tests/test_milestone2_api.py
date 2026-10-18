from io import BytesIO

from fastapi.testclient import TestClient
from PIL import Image

from app.main import app, get_visual_adapter
from app.services import minimind, qwen


class VisualStub:
    def analyze(self, path, prompt, structurer=None):
        assert path.exists()
        assert "只根据" in prompt
        return {"product_name": "坚果脆", "category": "零食", "colors": ["红色"], "materials": [], "scene": "桌面", "selling_points": ["便携"], "visible_text": ["海盐"], "risks": [], "page_layout": "上图下文", "visual_style": "简约"}


class QwenStub:
    def complete_json(self, system_prompt, user_prompt, temperature=0.3):
        if "审核" in system_prompt:
            return {"risks": [{"phrase": "最好", "level": "medium", "reason": "绝对化", "suggestion": "具体表述"}]}
        if "小红书" in system_prompt:
            return {"copy_variants": [{"title": "下午茶", "body": "一口酥脆", "tags": ["#零食"]}] * 3}
        if "只根据给定" in system_prompt:
            return {"answer": "避免绝对化表达"}
        return {"summary": "一款便携零食", "evidence": ["product/snack.md"]}

    def summarize(self, content, context):
        return self.complete_json("商品总结", content)

    def generate_copy(self, content, context):
        return self.complete_json("小红书", content)

    def review_copy(self, content, context):
        return self.complete_json("审核", content)


def test_visual_analysis_uses_uploaded_asset_and_material_type(monkeypatch):
    get_visual_adapter.cache_clear()
    monkeypatch.setattr(minimind, "MiniMindVAdapter", lambda: VisualStub())
    image = BytesIO()
    Image.new("RGB", (8, 8), "white").save(image, format="PNG")
    with TestClient(app) as client:
        upload = client.post("/api/uploads", files={"file": ("snack.png", image.getvalue(), "image/png")})
        response = client.post("/api/analysis/visual", json={"asset_id": upload.json()["asset_id"], "material_type": "competitor"})
    assert response.status_code == 200
    assert response.json()["analysis"]["product_name"] == "坚果脆"
    assert response.json()["analysis"]["page_layout"] == "上图下文"
    assert response.json()["material_type"] == "competitor"
    get_visual_adapter.cache_clear()


def test_visual_adapter_is_reused_within_process(monkeypatch):
    get_visual_adapter.cache_clear()
    created = []
    monkeypatch.setattr(minimind, "MiniMindVAdapter", lambda: created.append(VisualStub()) or created[-1])
    assert get_visual_adapter() is get_visual_adapter()
    assert len(created) == 1
    get_visual_adapter.cache_clear()


def test_visual_analysis_rejects_invalid_image_before_model_load(monkeypatch):
    get_visual_adapter.cache_clear()
    monkeypatch.setattr(minimind, "MiniMindVAdapter", lambda: (_ for _ in ()).throw(AssertionError("model should not load")))
    with TestClient(app) as client:
        upload = client.post("/api/uploads", files={"file": ("fake.png", b"not an image", "image/png")})
        response = client.post("/api/analysis/visual", json={"asset_id": upload.json()["asset_id"], "material_type": "product"})
    assert response.status_code == 400
    get_visual_adapter.cache_clear()


def test_text_tasks_have_distinct_structured_results(monkeypatch):
    monkeypatch.setattr(qwen, "QwenAdapter", lambda: QwenStub())
    with TestClient(app) as client:
        summary = client.post("/api/text/generate", json={"task": "summary", "content": "海盐坚果脆"})
        copy = client.post("/api/text/generate", json={"task": "copy", "content": "海盐坚果脆"})
        review = client.post("/api/text/generate", json={"task": "review", "content": "最好吃"})
    assert summary.json()["result"]["summary"] == "一款便携零食"
    assert len(copy.json()["result"]["copy_variants"]) == 3
    assert review.json()["result"]["risks"][0]["phrase"] == "最好"


def test_rag_index_and_ask_return_evidence(monkeypatch):
    monkeypatch.setattr(qwen, "QwenAdapter", lambda: QwenStub())
    with TestClient(app) as client:
        index = client.post("/api/rag/index")
        answer = client.post("/api/rag/ask", json={"question": "小红书零食文案要避免什么表达？", "collection": "platform", "top_k": 2})
    assert index.status_code == 200
    assert index.json()["total_chunks"] >= 4
    assert answer.status_code == 200
    assert answer.json()["evidence"]
    assert answer.json()["evidence"][0]["collection"] == "platform"
    assert answer.json()["answer"] == "避免绝对化表达"


def test_rag_query_returns_evidence_without_qwen_key(monkeypatch):
    monkeypatch.delenv("DASHSCOPE_API_KEY", raising=False)
    with TestClient(app) as client:
        client.post("/api/rag/index")
        response = client.post("/api/rag/query", json={"question": "避免绝对化用语", "collection": "brand", "top_k": 2})
    assert response.status_code == 200
    assert response.json()["hits"]
    assert response.json()["hits"][0]["collection"] == "brand"
    assert response.json()["hits"][0]["score"] > 0


def test_unconfigured_qwen_returns_503(monkeypatch):
    monkeypatch.delenv("DASHSCOPE_API_KEY", raising=False)
    with TestClient(app) as client:
        response = client.post("/api/text/generate", json={"task": "summary", "content": "海盐坚果脆"})
    assert response.status_code == 503
    assert "DASHSCOPE_API_KEY" in response.json()["detail"]
