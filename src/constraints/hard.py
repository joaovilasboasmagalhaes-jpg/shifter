from model.schedule import Schedule


def five_consecutive_shifts(schedule: Schedule) -> bool:
    """Ensure that no worker has more than 5 consecutive shifts.
    Returns True if any worker has more than 5 consecutive shifts, else False."""
    for worker_id, shifts in schedule.shifts_by_worker.items():
        # Sort shifts by date to check for consecutive days
        sorted_shifts = sorted(shifts, key=lambda s: s.date)
        consecutive_count = 1

        for i in range(1, len(sorted_shifts)):
            if (sorted_shifts[i].date - sorted_shifts[i - 1].date).days == 1:
                consecutive_count += 1
                if consecutive_count > 5:
                    return True
            else:
                consecutive_count = 1

    return False
