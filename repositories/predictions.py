from dataclasses import dataclass

from models import PredictionRequest


@dataclass(frozen=True)
class Prediction:
    item: PredictionRequest
    has_violations: bool


class PredictionRepository:
    """Последняя проверка каждого объявления; данные живут до перезапуска."""

    def __init__(self) -> None:
        self._predictions: dict[int, Prediction] = {}

    def save(self, item: PredictionRequest, has_violations: bool) -> None:
        self._predictions[item.item_id] = Prediction(
            item=item.model_copy(deep=True), has_violations=has_violations
        )

    def get(self, item_id: int) -> Prediction | None:
        prediction = self._predictions.get(item_id)
        if prediction is None:
            return None
        return Prediction(
            item=prediction.item.model_copy(deep=True),
            has_violations=prediction.has_violations,
        )
