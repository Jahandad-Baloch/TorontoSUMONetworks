# modules/core/app_context.py
from modules.common.utils import ConfigLoader, LoggerSetup
from pathlib import Path

class AppContext:
    """
    Application context for simulation tasks.
    This class loads the configuration, sets up the logger, and stores common paths and settings.
    
    Attributes:
        config (dict): Loaded configuration settings.
        logger (logging.Logger): Configured logger instance.
    """

    def __init__(self, config_path: str = 'configurations/main_config.yaml'):

        """
        Initializes the AppContext.

        Args:
            config_path (str): Path to the YAML configuration file.
        """
        self.config = ConfigLoader.load_config(config_path)
        self.logger = LoggerSetup.setup_logger(
            'main',
            self.config['logging']['log_dir'],
            self.config['logging']['log_level']
        )
        # Optionally, use pathlib for path handling:
        self.paths = {key: Path(val) for key, val in self.config['paths'].items()}
