import pytest
from fastapi.testclient import TestClient

from main import create_app
from models import PredictionRequest
from repositories.predictions import PredictionRepository


@pytest.fixture
def payload():
    return {
        "seller_id": 1,
        "is_verified_seller": False,
        "item_id": 42,
        "name": "Велосипед",
        "description": "Городской велосипед, пробег 200 км",
        "category": 3,
        "images_qty": 0,
    }


@pytest.fixture
def item(payload):
    return PredictionRequest(**payload)


@pytest.fixture
def repository():
    return PredictionRepository()


@pytest.fixture
def app():
    return create_app()


@pytest.fixture
def client(app):
    # Позволяет проверить настоящий HTTP-ответ обработчика ошибок.
    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client
