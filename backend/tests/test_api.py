from io import BytesIO

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_upload_and_create_task_returns_four_stage_result():
    upload = client.post(
        "/api/uploads",
        files={"file": ("snack.jpg", BytesIO(b"image-bytes"), "image/jpeg")},
    )
    assert upload.status_code == 200
    asset_id = upload.json()["asset_id"]

    response = client.post(
        "/api/tasks",
        json={
            "asset_id": asset_id,
            "platform": "xiaohongshu",
            "category": "snack",
            "brief": "突出下午茶和便携",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "completed"
    assert [stage["stage"] for stage in body["stages"]] == [
        "material_analysis",
        "copy_generation",
        "content_review",
        "auto_rewrite",
    ]
    assert len(body["result"]["copy_variants"]) == 3


def test_upload_rejects_unsupported_type():
    response = client.post(
        "/api/uploads",
        files={"file": ("notes.txt", BytesIO(b"not-image"), "text/plain")},
    )

    assert response.status_code == 400
    assert "image" in response.json()["detail"]


def test_create_task_rejects_empty_brief():
    response = client.post(
        "/api/tasks",
        json={
            "asset_id": "asset_missing",
            "platform": "xiaohongshu",
            "category": "snack",
            "brief": "   ",
        },
    )

    assert response.status_code == 422


def test_unknown_task_returns_not_found():
    response = client.get("/api/tasks/task_missing")

    assert response.status_code == 404
    assert response.json()["detail"] == "Task not found"
