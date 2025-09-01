
from abc import ABC, abstractmethod

class BaseArchiver(ABC):
    """
    An abstract base class for archivers.
    """

    def __init__(self, command):
        self.command = command

    @abstractmethod
    def run(self):
        """The main public method that orchestrates the archiving process."""
        pass
