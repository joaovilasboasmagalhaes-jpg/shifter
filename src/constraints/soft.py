
from collections import defaultdict

try:
    from model.schedule import Schedule
    from model.shift_type import ShiftWorkType
except ModuleNotFoundError:
    from src.model.schedule import Schedule
    from src.model.shift_type import ShiftWorkType


def balanced_schedule(schedule: Schedule) -> float:
    """Score the schedule based on how balanced the shifts are among workers."""
    shift_type_codes = [shift_type.code for shift_type in ShiftWorkType]
    WEIGHTS: dict[int, float] = {stc: 1.0 for stc in shift_type_codes}  # Equal weight for all shift types
    
    # Count the number of each shift type assigned to each worker
    counts: dict[int, list[int]] = defaultdict(lambda: [0, 0, 0])
    for worker_id, shifts in schedule.shifts_by_worker.items():
        for shift in shifts:
            if shift.is_work_shift():
                stc = shift.shift_type.code
                counts[worker_id][stc] += 1
    
    # Calculate the average number of each shift type per worker
    average: dict[int, float] = {}
    for stc in shift_type_codes:
        total = sum(counts[worker_id][stc] for worker_id in counts)
        average[stc] = total / len(counts) if counts else 0.0
    
    # Calculate the imbalance score as the sum of absolute deviations from the average
    imbalance_score = 0.0
    for worker_id in counts:
        worker_score = 0.0
        for stc in shift_type_codes:
            worker_score += WEIGHTS[stc] * abs(counts[worker_id][stc] - average[stc])

        imbalance_score += worker_score
    
    return imbalance_score