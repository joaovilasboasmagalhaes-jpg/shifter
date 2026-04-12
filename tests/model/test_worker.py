from src.model.worker import Worker


def test_worker_to_string_and_str():
    Worker.reset_ids()
    w = Worker(name="Alice")
    assert w.id == 1
    assert w.name == "Alice"
    assert w.to_string() == "Alice"
    assert str(w) == "Alice"


def test_worker_hash_uses_name_and_id():
    Worker.reset_ids()
    w = Worker(name="Alice")

    assert hash(w) == hash((w.name, w.id))


def test_worker_hash_tracks_fields_used_by_equality():
    Worker.reset_ids()
    w1 = Worker(name="Alice")
    w2 = Worker(name="Alice")

    assert w1 != w2
    assert hash(w1) == hash((w1.name, w1.id))
    assert hash(w2) == hash((w2.name, w2.id))
