from unittest.mock import Mock

import pytest

from repositories.predictions import PredictionRepository
from services.moderation import ModerationService


@pytest.mark.parametrize(
    ("verified", "images_qty", "expected"),
    [(False, 0, True), (False, 1, False), (True, 0, False), (True, 1, False)],
)
def test_predict_and_save(item, verified, images_qty, expected):
    item.is_verified_seller = verified
    item.images_qty = images_qty
    repository = Mock(spec=PredictionRepository)
    service = ModerationService(repository)

    assert service.predict(item) is expected
    repository.save.assert_called_once_with(item, expected)


def test_storage_failure_is_not_a_prediction(item):
    repository = Mock(spec=PredictionRepository)
    repository.save.side_effect = RuntimeError("Storage unavailable")

    with pytest.raises(RuntimeError, match="Storage unavailable"):
        ModerationService(repository).predict(item)
