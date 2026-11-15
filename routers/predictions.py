from typing import Annotated

from fastapi import APIRouter, Depends, Request

from models import PredictionRequest, ServerErrorResponse, ValidationErrorResponse
from services.moderation import ModerationService

router = APIRouter()


def get_moderation_service(request: Request) -> ModerationService:
    return request.app.state.moderation_service


@router.post(
    "/predict",
    response_model=bool,
    summary="Проверить объявление на нарушения",
    description="true — есть нарушения; false — нарушений нет.",
    responses={
        400: {"model": ValidationErrorResponse, "description": "Некорректный запрос"},
        500: {"model": ServerErrorResponse, "description": "Внутренняя ошибка сервера"},
    },
)
def predict(
    item: PredictionRequest,
    service: Annotated[ModerationService, Depends(get_moderation_service)],
) -> bool:
    return service.predict(item)
