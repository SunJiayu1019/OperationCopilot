from pathlib import Path

from PIL import Image
import torch

from app.services.minimind import MiniMindVAdapter
from app.services.errors import ModelOutputError


class FakeTokenizer:
    pad_token_id = 0
    eos_token_id = 2

    def apply_chat_template(self, messages, tokenize=False, add_generation_prompt=True):
        return messages[0]["content"]

    def __call__(self, text, return_tensors):
        return {"input_ids": torch.tensor([[1, 2]]), "attention_mask": torch.tensor([[1, 1]])}


class FakeProcessor:
    def __call__(self, images, return_tensors):
        assert images.mode == "RGB"
        return {"pixel_values": torch.zeros((1, 3, 8, 8))}


class FakeModel:
    class Config:
        image_special_token = "<image>"
        image_token_len = 1

    config = Config()

    def generate(self, **kwargs):
        return '{"product_name":"海盐坚果脆","category":"零食","colors":[],"materials":[],"scene":"桌面","selling_points":["酥脆"],"visible_text":[],"risks":[]}'


def test_minimind_adapter_parses_structured_visual_result(tmp_path: Path):
    image_path = tmp_path / "snack.jpg"
    Image.new("RGB", (8, 8), "white").save(image_path)
    adapter = MiniMindVAdapter(model=FakeModel(), tokenizer=FakeTokenizer(), processor=FakeProcessor())

    result = adapter.analyze(image_path, "请分析图片")

    assert result["product_name"] == "海盐坚果脆"
    assert result["category"] == "零食"
    assert result["page_layout"] == "unknown"


def test_minimind_rejects_missing_required_fields(tmp_path: Path):
    image_path = tmp_path / "snack.jpg"
    Image.new("RGB", (8, 8), "white").save(image_path)
    model = FakeModel()
    model.generate = lambda **kwargs: '{"product_name":"海盐坚果脆"}'
    adapter = MiniMindVAdapter(model=model, tokenizer=FakeTokenizer(), processor=FakeProcessor())
    try:
        adapter.analyze(image_path, "请分析图片")
    except ModelOutputError:
        pass
    else:
        raise AssertionError("expected invalid visual result error")


def test_minimind_uses_text_structurer_when_visual_model_returns_prose(tmp_path: Path):
    image_path = tmp_path / "snack.jpg"
    Image.new("RGB", (8, 8), "white").save(image_path)
    model = FakeModel()
    model.generate = lambda **kwargs: "图片中是一袋红色包装的零食"
    expected = {"product_name": "unknown", "category": "零食", "colors": ["红色"], "materials": [], "scene": "unknown", "selling_points": [], "visible_text": [], "risks": []}
    captured = []
    adapter = MiniMindVAdapter(model=model, tokenizer=FakeTokenizer(), processor=FakeProcessor())

    result = adapter.analyze(image_path, "请分析图片", structurer=lambda raw: captured.append(raw) or expected)

    assert captured == ["图片中是一袋红色包装的零食"]
    assert result["colors"] == ["红色"]
    assert result["raw_description"] == captured[0]


def test_minimind_structures_incomplete_json_when_available(tmp_path: Path):
    image_path = tmp_path / "snack.jpg"
    Image.new("RGB", (8, 8), "white").save(image_path)
    model = FakeModel()
    model.generate = lambda **kwargs: '{"product_name":"海盐坚果脆"}'
    adapter = MiniMindVAdapter(model=model, tokenizer=FakeTokenizer(), processor=FakeProcessor())
    complete = {"product_name": "海盐坚果脆", "category": "零食", "colors": [], "materials": [], "scene": "unknown", "selling_points": [], "visible_text": [], "risks": []}

    result = adapter.analyze(image_path, "请分析图片", structurer=lambda raw: complete)

    assert result["category"] == "零食"
