# modules/core/simulation_task.py
from abc import ABC, abstractmethod
# from modules.core.app_context import AppContext

class SimulationTask(ABC):
    """Abstract base class representing a single simulation pipeline task.

    Each subclass must implement the execute() method.
    """
    # def __init__(self, app_context: AppContext) -> None:
    def __init__(self, app_context) -> None:
        """
        Initializes the SimulationTask.

        Args:
            app_context (AppContext): Central application context with configuration and logger.
        """
        self.app_context = app_context
        self.config = app_context.config
        self.logger = app_context.logger

    @abstractmethod
    def execute(self) -> None:
        """Executes the task. Must be overridden by subclasses."""
        pass
