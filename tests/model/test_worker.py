from src.model.worker import Worker


def test_worker_to_string_and_str():
    Worker.reset_ids()
    w = Worker(name="Alice")
    assert w.id == 1
    assert w.name == "Alice"
    assert w.to_string() == "Alice"
    assert str(w) == "Alice"
