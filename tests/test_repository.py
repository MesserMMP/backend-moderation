from repositories.predictions import PredictionRepository


def test_unknown_item(repository):
    assert repository.get(42) is None


def test_save_and_read(repository, item):
    repository.save(item, True)
    stored = repository.get(item.item_id)
    assert stored.item == item
    assert stored.has_violations is True


def test_update_keeps_other_items(repository, item):
    second = item.model_copy(update={"item_id": 43})
    repository.save(item, True)
    repository.save(second, True)
    item.images_qty = 1
    repository.save(item, False)

    assert repository.get(item.item_id).has_violations is False
    assert repository.get(item.item_id).item.images_qty == 1
    assert repository.get(second.item_id).has_violations is True


def test_repositories_do_not_share_state(repository, item):
    repository.save(item, True)
    assert PredictionRepository().get(item.item_id) is None


def test_caller_cannot_mutate_stored_item(repository, item):
    repository.save(item, True)
    item.name = "Изменено снаружи"
    stored = repository.get(item.item_id)
    assert stored.item.name == "Велосипед"

    stored.item.name = "Изменена полученная копия"
    assert repository.get(item.item_id).item.name == "Велосипед"
