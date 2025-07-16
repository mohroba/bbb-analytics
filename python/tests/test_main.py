import json
from fastapi.testclient import TestClient
from pathlib import Path
import os
import importlib


def create_dummy_environment(tmp_path: Path):
    learning_dir = tmp_path / "learning-dashboard"
    meeting_dir = learning_dir / "m1" / "token123"
    meeting_dir.mkdir(parents=True)
    raw_data = {
        "name": "Demo Meeting",
        "createdOn": "2023-01-01",
        "endedOn": "2023-01-02"
    }
    (meeting_dir / "learning_dashboard_data.json").write_text(json.dumps(raw_data))

    analytics_file = tmp_path / "data.json"
    analytics_file.write_text(json.dumps({"analytics": []}))

    return learning_dir, analytics_file


def test_get_analytics_url(tmp_path, monkeypatch):
    learning_dir, analytics_file = create_dummy_environment(tmp_path)
    monkeypatch.setenv("LEARNING_DASHBOARD_DIR", str(learning_dir))
    monkeypatch.setenv("ANALYTICS_DATA_PATH", str(analytics_file))

    # Reload module to pick up env vars
    import app.main as main
    importlib.reload(main)

    client = TestClient(main.app)
    response = client.get("/analytics/m1")
    assert response.status_code == 200
    assert response.json()["url"] == "/learning-analytics-dashboard/?meeting=m1&report=token123"

    data = json.loads(analytics_file.read_text())
    assert len(data["analytics"]) == 1
    assert data["analytics"][0]["meetingId"] == "m1"
    assert data["analytics"][0]["token"] == "token123"
