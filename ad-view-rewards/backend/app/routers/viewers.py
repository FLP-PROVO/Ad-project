from fastapi import APIRouter

router = APIRouter()


@router.get(
    "",
    summary="Viewers placeholder",
    response_model=dict[str, str],
    responses={
        200: {
            "description": "Viewers placeholder response",
            "content": {
                "application/json": {
                    "examples": {
                        "placeholder": {
                            "value": {"message": "viewers router placeholder"}
                        }
                    }
                }
            },
        }
    },
)
def viewers_placeholder() -> dict[str, str]:
    return {"message": "viewers router placeholder"}
