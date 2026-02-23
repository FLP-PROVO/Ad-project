from fastapi import APIRouter

router = APIRouter()


@router.get("", summary="Viewers placeholder")
def viewers_placeholder() -> dict[str, str]:
    return {"message": "viewers router placeholder"}
