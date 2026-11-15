from models import PredictionRequest
from repositories.predictions import PredictionRepository


class ModerationService:
    def __init__(self, repository: PredictionRepository) -> None:
        self.repository = repository

    def predict(self, item: PredictionRequest) -> bool:
        has_violations = not item.is_verified_seller and item.images_qty == 0
        self.repository.save(item, has_violations)
        return has_violations
