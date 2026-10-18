from io import BytesIO

from fastapi.testclient import TestClient
from PIL import Image

from app.main import app
from app.services.agent import Agent, AgentError, ToolRegistry


class Planner:
    def __init__(self, actions):
        self.actions = iter(actions)

    def complete_json(self, system_prompt, user_prompt, temperature=0.3):
        if "意图分类" in system_prompt:
            return {"intent": "campaign"}
        return {"tool": next(self.actions)}


def test_campaign_selects_registered_tools_and_emits_steps():
    names = ["analyze_image", "search_knowledge", "generate_copy", "review_copy", "rewrite_copy"]
    registry = ToolRegistry()
    for name in names:
        registry.register(name, lambda state, name=name: {"value": name})
    events = []
    result = Agent(Planner(names), registry).run("写一篇下午茶文案", "asset_1", events.append)
    assert list(result["observations"]) == names
    assert [event["status"] for event in events] == [status for _ in names for status in ("running", "completed")]


def test_agent_rejects_out_of_order_and_unknown_tool():
    registry = ToolRegistry()
    registry.register("analyze_image", lambda state: {})
    for action in ("rewrite_copy", "anything"):
        try:
            Agent(Planner([action]), registry).run("生成文案", "asset_1", lambda event: None)
        except AgentError as error:
            assert "tool" in str(error).lower()
        else:
            raise AssertionError("invalid tool selection must fail")


def test_agent_has_step_limit():
    registry = ToolRegistry()
    registry.register("search_knowledge", lambda state: {})
    class RepeatingPlanner(Planner):
        def complete_json(self, system_prompt, user_prompt, temperature=0.3):
            return {"intent": "campaign"} if "意图分类" in system_prompt else {"tool": "search_knowledge"}
    try:
        Agent(RepeatingPlanner([]), registry).run("规则?", "asset_1", lambda event: None)
    except AgentError:
        pass
    else:
        raise AssertionError("repeated action must fail")


def test_chat_api_validates_asset_and_reports_background_failure(monkeypatch):
    from app import main
    monkeypatch.setattr(main, "build_agent", lambda: (_ for _ in ()).throw(RuntimeError("secret exception")))
    with TestClient(app) as client:
        missing = client.post("/api/chat/tasks", json={"message": "分析图片", "asset_id": "missing"})
        assert missing.status_code == 404
        image = BytesIO()
        Image.new("RGB", (8, 8), "white").save(image, format="PNG")
        upload = client.post("/api/uploads", files={"file": ("image.png", image.getvalue(), "image/png")}).json()
        created = client.post("/api/chat/tasks", json={"message": "分析图片", "asset_id": upload["asset_id"]})
        assert created.status_code == 202
        fetched = client.get(f'/api/chat/tasks/{created.json()["id"]}')
        assert fetched.status_code == 200
        assert client.get("/api/chat/tasks/missing").status_code == 404
