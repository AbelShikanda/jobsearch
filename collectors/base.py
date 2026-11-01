from abc import ABC, abstractmethod
from models import Job


class BaseCollector(ABC):
    name: str = "base"

    @abstractmethod
    def fetch(self) -> list[Job]:
        ...