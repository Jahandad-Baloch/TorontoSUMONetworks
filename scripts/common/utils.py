import os
import yaml
import logging
from datetime import datetime
import pandas as pd

"""
This module contains utility functions for network building.
"""

class ConfigLoader:
    @staticmethod
    def load_config(config_path):
        """
        Load configuration from a YAML file.

        Args:
            config_path (str): Path to the configuration file.

        Returns:
            dict: Loaded configuration.
        """
        with open(config_path) as file:
            configs = yaml.full_load(file)
            base_path = os.path.dirname(config_path)
            for conf in configs.get('imports', []):
                conf_path = os.path.join(base_path, conf)
                with open(conf_path) as f:
                    configs.update(yaml.full_load(f))
            return configs

class FileIO:
    @staticmethod
    def save_to_csv(data: pd.DataFrame, path: str, logger):
        data.to_csv(path, index=False)
        logger.info(f"Data saved to {path}")


class LoggerSetup:
    @staticmethod
    def setup_logger(name, log_dir, level=logging.INFO):
        """
        Setup a logger with the specified name and log directory.

        Args:
            name (str): Name of the logger.
            log_dir (str): Directory to store log files.
            level (int, optional): Logging level. Defaults to logging.INFO.

        Returns:
            logging.Logger: Configured logger.
        """
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        log_file = os.path.join(log_dir, f"{name}_{datetime.now().strftime('%m%d')}.log")
        
        handler = logging.FileHandler(log_file)
        formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
        handler.setFormatter(formatter)

        logger = logging.getLogger(name)
        logger.setLevel(level)
        logger.addHandler(handler)

        return logger






