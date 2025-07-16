import os
import json
import glob
import logging
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

LEARNING_DASHBOARD_DIR = os.getenv("LEARNING_DASHBOARD_DIR", "/var/bigbluebutton/learning-dashboard")
ANALYTICS_DATA_PATH = os.getenv("ANALYTICS_DATA_PATH", "/var/www/bigbluebutton-default/analytics/data.json")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

class AnalyticsURL(BaseModel):
    url: str


def _read_json(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _write_json(path: str, data: dict) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f)


@app.get("/analytics/{meeting_id}", response_model=AnalyticsURL)
def get_analytics_url(meeting_id: str) -> AnalyticsURL:
    """Return dashboard URL for a meeting and update analytics data."""
    try:
        token_paths = glob.glob(os.path.join(LEARNING_DASHBOARD_DIR, meeting_id, "*"))
        if not token_paths:
            raise FileNotFoundError("Token directory not found")

        token_dir = token_paths[0]
        token = os.path.basename(token_dir)
        data_file = os.path.join(token_dir, "learning_dashboard_data.json")
        raw_data = _read_json(data_file)

        analytics_entry = {
            "name": raw_data.get("name"),
            "meetingId": meeting_id,
            "token": token,
            "createdOn": raw_data.get("createdOn"),
            "endedOn": raw_data.get("endedOn"),
        }

        if os.path.exists(ANALYTICS_DATA_PATH):
            analytics_root = _read_json(ANALYTICS_DATA_PATH)
        else:
            analytics_root = {"analytics": []}

        analytics_root.setdefault("analytics", []).append(analytics_entry)
        _write_json(ANALYTICS_DATA_PATH, analytics_root)

        url = f"/learning-analytics-dashboard/?meeting={meeting_id}&report={token}"
        logger.info("Analytics updated for %s", meeting_id)
        return AnalyticsURL(url=url)
    except Exception as exc:  # pylint: disable=broad-except
        logger.error("Failed to process meeting %s: %s", meeting_id, exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000)
