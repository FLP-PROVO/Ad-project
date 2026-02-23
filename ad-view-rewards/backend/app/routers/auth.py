from fastapi import APIRouter

router = APIRouter()


@router.get("", summary="Auth placeholder")
def auth_placeholder() -> dict[str, str]:
    return {"message": "auth router placeholder"}
