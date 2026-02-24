import json
from pathlib import Path

from fastapi import FastAPI

from app.routers import admin_ads, admin_gift_codes, ads, auth, media_stream, users, viewers

app = FastAPI(title="Ad View Rewards API", version="0.1.0")


@app.get(
    "/api/v1/health",
    tags=["health"],
    response_model=dict[str, str],
    responses={
        200: {
            "description": "Service health status",
            "content": {
                "application/json": {
                    "examples": {
                        "healthy": {
                            "summary": "Healthy response",
                            "value": {"status": "ok"},
                        }
                    }
                }
            },
        }
    },
)
def health_check() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
app.include_router(viewers.router, prefix="/api/v1/viewers", tags=["viewers"])
app.include_router(ads.router, prefix="/api/v1/ads", tags=["ads"])
app.include_router(media_stream.router, prefix="/media", tags=["media"])

app.include_router(admin_ads.router, prefix="/api/v1/admin", tags=["admin-ads"])

app.include_router(admin_gift_codes.router, prefix="/api/v1/admin", tags=["admin-gift-codes"])


def export_openapi_json(output_path: Path) -> Path:
    output_path.write_text(json.dumps(app.openapi(), indent=2), encoding="utf-8")
    return output_path
