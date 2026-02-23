from fastapi import FastAPI

from app.routers import ads, auth, viewers

app = FastAPI(title="Ad View Rewards API", version="0.1.0")


@app.get("/api/v1/health", tags=["health"])
def health_check() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(viewers.router, prefix="/api/v1/viewers", tags=["viewers"])
app.include_router(ads.router, prefix="/api/v1/ads", tags=["ads"])
