from unittest.mock import Mock

import pytest

from models import ValidationErrorResponse
from services.moderation import ModerationService


@pytest.mark.parametrize(
    ("verified", "images_qty", "expected"),
    [(False, 0, True), (False, 1, False), (False, 5, False), (True, 0, False), (True, 1, False)],
)
def test_predict(client, payload, verified, images_qty, expected):
    payload.update(is_verified_seller=verified, images_qty=images_qty)

    response = client.post("/predict", json=payload)

    assert response.status_code == 200
    assert response.json() is expected
    assert response.headers["content-type"] == "application/json"


@pytest.mark.parametrize(
    "field",
    ["seller_id", "is_verified_seller", "item_id", "name", "description", "category", "images_qty"],
)
def test_required_fields(client, payload, field):
    del payload[field]

    response = client.post("/predict", json=payload)

    assert response.status_code == 400
    assert response.json()["detail"][0]["loc"] == ["body", field]
    assert response.json()["detail"][0]["type"] == "missing"


@pytest.mark.parametrize("field", ["seller_id", "item_id", "category", "images_qty"])
@pytest.mark.parametrize("value", ["1", 1.5, True, None, [], {}])
def test_integer_types_are_strict(client, payload, field, value):
    payload[field] = value

    response = client.post("/predict", json=payload)

    assert response.status_code == 400
    assert response.json()["detail"][0]["loc"] == ["body", field]


@pytest.mark.parametrize("value", ["true", "false", 0, 1, None, [], {}])
def test_boolean_type_is_strict(client, payload, value):
    payload["is_verified_seller"] = value
    assert client.post("/predict", json=payload).status_code == 400


@pytest.mark.parametrize("field", ["name", "description"])
@pytest.mark.parametrize("value", [12, False, None, [], {}, "", " \t\n "])
def test_text_fields(client, payload, field, value):
    payload[field] = value
    assert client.post("/predict", json=payload).status_code == 400


@pytest.mark.parametrize("field", ["seller_id", "item_id", "category"])
@pytest.mark.parametrize("value", [0, -1])
def test_identifiers_are_positive(client, payload, field, value):
    payload[field] = value
    assert client.post("/predict", json=payload).status_code == 400


def test_negative_images_qty(client, payload):
    payload["images_qty"] = -1
    assert client.post("/predict", json=payload).status_code == 400


def test_unknown_field(client, payload):
    payload["images_quantity"] = 1
    response = client.post("/predict", json=payload)
    assert response.status_code == 400
    assert response.json()["detail"][0]["type"] == "extra_forbidden"


@pytest.mark.parametrize("body", ["", "{", "null", "[]", '"text"', "42", "true"])
def test_invalid_request_body(client, body):
    response = client.post("/predict", content=body, headers={"Content-Type": "application/json"})
    assert response.status_code == 400
    assert isinstance(response.json()["detail"], list)
    ValidationErrorResponse.model_validate(response.json())


def test_invalid_utf8_body(client):
    response = client.post(
        "/predict", content=b"\xff", headers={"Content-Type": "application/json"}
    )
    assert response.status_code == 400
    ValidationErrorResponse.model_validate(response.json())


def test_validation_does_not_call_service(client, app, payload):
    service = Mock(spec=ModerationService)
    app.state.moderation_service = service
    payload["images_qty"] = -1

    assert client.post("/predict", json=payload).status_code == 400
    service.predict.assert_not_called()


@pytest.mark.parametrize("failure_source", ["service", "repository"])
def test_internal_error(client, app, payload, monkeypatch, caplog, failure_source):
    service = app.state.moderation_service
    target, method = (
        (service, "predict") if failure_source == "service" else (service.repository, "save")
    )
    monkeypatch.setattr(target, method, Mock(side_effect=RuntimeError("private error details")))

    response = client.post("/predict", json=payload)

    assert response.status_code == 500
    assert response.json() == {"detail": "Internal server error"}
    assert "private error details" not in response.text
    assert "Prediction request failed" in caplog.text


def test_repeated_prediction_uses_current_input(client, payload):
    assert client.post("/predict", json=payload).json() is True
    payload["images_qty"] = 1
    assert client.post("/predict", json=payload).json() is False


def test_root(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello World"}


def test_wrong_method(client):
    assert client.get("/predict").status_code == 405


def test_openapi_matches_contract(client):
    schema = client.get("/openapi.json").json()
    responses = schema["paths"]["/predict"]["post"]["responses"]
    assert set(responses) == {"200", "400", "500"}
    assert responses["200"]["content"]["application/json"]["schema"]["type"] == "boolean"
    assert client.get("/openapi.json").json() == schema
