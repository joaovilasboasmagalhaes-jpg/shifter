from dataclasses import dataclass


@dataclass
class Worker:
    """A simple Worker model.

    Attributes:
        id: Unique identifier for the worker.
        name: Human-readable name for the worker.
    """

    id: int
    name: str

    def to_string(self) -> str:
        """Return the worker's name as a string."""
        return self.name

    def __str__(self) -> str:
        return self.to_string()
