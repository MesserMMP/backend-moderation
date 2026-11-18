import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse

from database import lifespan
from repositories.predictions import PredictionRepository
from routers.predictions import router
from services.moderation import ModerationService

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    app = FastAPI(title="Модерация объявлений", version="1.1.0", lifespan=lifespan)
    app.state.moderation_service = ModerationService(PredictionRepository())
    app.include_router(router)

    @app.get("/")
    def root() -> dict[str, str]:
        return {"message": "Hello World"}

    @app.exception_handler(RequestValidationError)
    async def invalid_request(request: Request, exc: RequestValidationError) -> JSONResponse:
        # Не возвращаем исходные данные клиента и внутренний контекст валидатора.
        errors = [
            {"loc": list(error["loc"]), "msg": error["msg"], "type": error["type"]}
            for error in exc.errors()
        ]
        return JSONResponse(status_code=400, content={"detail": errors})

    @app.exception_handler(Exception)
    async def server_error(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Prediction request failed", exc_info=exc)
        return JSONResponse(status_code=500, content={"detail": "Internal server error"})

    def custom_openapi() -> dict[str, Any]:
        if app.openapi_schema is None:
            schema = get_openapi(title=app.title, version=app.version, routes=app.routes)
            # Ошибки входных данных возвращаются как 400, а не стандартный 422.
            for path in ("/predict", "/simple_predict"):
                schema["paths"][path]["post"]["responses"].pop("422", None)
            app.openapi_schema = schema
        return app.openapi_schema

    app.openapi = custom_openapi
    return app


app = create_app()
