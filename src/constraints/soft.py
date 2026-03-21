from collections import defaultdict

try:
    from model.schedule import Schedule
    from model.shift_type import ShiftType, ShiftWorkType
except ModuleNotFoundError:
    from src.model.schedule import Schedule
    from src.model.shift_type import ShiftType, ShiftWorkType


def balanced_schedule(schedule: Schedule) -> float:
    """Score the schedule based on how balanced the shifts are among workers."""
    shift_codes = [shift_type.code for shift_type in ShiftWorkType]
    WEIGHTS: dict[int, float] = {
        stc: 1.0 for stc in shift_codes
    }  # Equal weight for all shift types

    # Count the number of each shift type assigned to each worker
    counts: dict[int, list[int]] = defaultdict(lambda: [0, 0, 0])
    for worker_id, shifts in schedule.shifts_by_worker.items():
        for shift in shifts:
            if shift.is_work_shift():
                stc = shift.shift_type.code
                counts[worker_id][stc] += 1
    
    # Calculate the average number of each shift type per worker
    average: dict[int, float] = {}
    for stc in shift_codes:
        total = sum(counts[worker_id][stc] for worker_id in counts)
        average[stc] = total / len(counts) if counts else 0.0
    
    # Calculate the imbalance score as the sum of absolute deviations from the average
    imbalance_score = 0.0
    for worker_id in counts:
        worker_score = 0.0
        for stc in shift_codes:
            worker_score += WEIGHTS[stc] * abs(counts[worker_id][stc] - average[stc])

        imbalance_score += worker_score
    
    return imbalance_score


def shift_continuation(schedule: Schedule) -> float:
    """Score the schedule based on number of shift changes in consecutive days for each worker."""
    shift_codes = [stc.code for sub in ShiftType.__subclasses__() for stc in sub]
    WEIGHTS_FROM_TO: dict[tuple[int, int], float] = {
        (shift_from, shift_to): 1.0
        for shift_from in shift_codes
        for shift_to in shift_codes
    }
    CHANGE_PENALTY = 1.0

    def penalty(from_shift: ShiftType, to_shift: ShiftType) -> float:
        if to_shift != from_shift:
            weight = WEIGHTS_FROM_TO.get((from_shift.code, to_shift.code), 1.0)
            return CHANGE_PENALTY * weight
        return 0.0

    worker_scores: dict[int, float] = {}
    for worker_id, shifts in schedule.shifts_by_worker.items():
        sorted_shifts = sorted(shifts, key=lambda s: s.date)
        worker_score = sum(
            penalty(sorted_shifts[i - 1].shift_type, sorted_shifts[i].shift_type)
            for i in range(1, len(sorted_shifts))
            if sorted_shifts[i].consecutive_shifts(sorted_shifts[i - 1])
        )
        worker_scores[worker_id] = worker_score

    shift_continuation_score = sum(worker_scores.values())
    return shift_continuation_score