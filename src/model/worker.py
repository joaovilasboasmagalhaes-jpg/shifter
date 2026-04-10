from dataclasses import dataclass, field
from typing import ClassVar


@dataclass
class Worker:
    """A simple Worker model.

    Attributes:
        name: Human-readable name for the worker.
        id: Unique identifier for the worker, auto-generated.
    """

    name: str
    id: int = field(init=False)

    _last_id: ClassVar[int] = 0

    def __post_init__(self) -> None:
        """Generate a sequential id, one greater than the previously created worker."""
        type(self)._last_id += 1
        self.id = type(self)._last_id

    @classmethod
    def reset_ids(cls) -> None:
        """Reset the internal id counter.

        Primarily useful for tests to keep ids deterministic.
        """
        cls._last_id = 0

    def to_string(self) -> str:
        """Return the worker's name as a string."""
        return self.name

    def __str__(self) -> str:
        return self.to_string()

    def __hash__(self) -> int:
        """Hash by the same fields used for dataclass equality."""
        return hash((self.name, self.id))
