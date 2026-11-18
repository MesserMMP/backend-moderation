from typing import Annotated

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, Query, Request

from database import get_connection
from models import PredictionRequest, ServerErrorResponse, ValidationErrorResponse
from repositories.items import ItemRepository
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


@router.post(
    "/simple_predict",
    summary="Проверить объявление по идентификатору",
    responses={
        400: {"model": ValidationErrorResponse},
        404: {"model": ServerErrorResponse, "description": "Объявление не найдено"},
        500: {"model": ServerErrorResponse},
    },
)
async def simple_predict(
    item_id: Annotated[int, Query(gt=0, le=2**63 - 1)],
    service: Annotated[ModerationService, Depends(get_moderation_service)],
    connection: Annotated[asyncpg.Connection, Depends(get_connection)],
) -> bool:
    item = await ItemRepository(connection).for_prediction(item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Объявление не найдено")
    return service.predict(item)
