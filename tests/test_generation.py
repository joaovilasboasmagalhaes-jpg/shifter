from datetime import date

from src.generation.generator import generate
from src.model.shift_type import ShiftWorkType
from src.model.worker import Worker


def test_generate_april_2026_with_five_workers_smoke():
    """Smoke test for debugging the high-level generation entry point.

    This test intentionally uses a concrete month and a small worker pool so it
    is easy to set breakpoints and step through the full generation cycle.
    """
    Worker.reset_ids()
    workers = [Worker(f"Worker {index}") for index in range(1, 6)]

    schedule = generate(
        workers=workers,
        start_date=date(2026, 4, 1),
        end_date=date(2026, 4, 30),
    )

    expected_total_shifts = 30 * len(list(ShiftWorkType))

    assert schedule.start_date == date(2026, 4, 1)
    assert schedule.end_date == date(2026, 4, 30)
    assert sum(len(shifts) for shifts in schedule.shifts_by_worker.values()) == expected_total_shifts
    assert {worker.id for worker in schedule.get_workers()} == {worker.id for worker in workers}
