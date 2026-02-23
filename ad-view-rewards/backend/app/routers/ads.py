from fastapi import APIRouter

router = APIRouter()


@router.get("", summary="Ads placeholder")
def ads_placeholder() -> dict[str, str]:
    return {"message": "ads router placeholder"}
