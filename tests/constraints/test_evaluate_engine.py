from datetime import date

from src.constraints.constraints_engine import evaluate
from src.model.schedule import Schedule
from src.model.shift import Shift
from src.model.shift_type import ShiftWorkType
from src.model.worker import Worker


def test_evaluate():
    # Create a worker
    worker = Worker(name="Alice")

    # Create a schedule for February 2026
    start = date(2026, 2, 1)
    end = date(2026, 2, 28)
    schedule = Schedule(start_date=start, end_date=end)

    # Add a single morning shift for the worker
    shift = Shift(shift_type=ShiftWorkType.MORNING, date=start, worker=worker)
    schedule.add_shift(shift)

    # Evaluate constraints
    evaluate(schedule)
    print("evaluate ran without error")

if __name__ == "__main__":
    test_evaluate()
