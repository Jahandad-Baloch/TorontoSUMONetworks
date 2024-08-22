import subprocess
import os

""" 
This script is used to execute commands.
path: scripts/common/command_executor.py
"""

class CommandExecutor:
    def __init__(self, logger=None):
        """
        Initializes the CommandExecutor.

        Args:
            logger (logging.Logger): Optional logger for logging command output. If None, a default logger will be used.
        """
        self.logger = logger

    def run_command(self, command, shell=False, capture_output=True, check=True, cwd=None, env=None):
        """
        Executes a command using subprocess and logs the output.

        Args:
            command (str or list): Command to execute.
            shell (bool): Whether to use the shell as the program to execute. Defaults to False.
            capture_output (bool): Whether to capture stdout and stderr. Defaults to True.
            check (bool): If True, raise an exception on command failure. Defaults to True.
            cwd (str): If not None, change to this directory before running the command.
            env (dict): Environment variables to use for the command.

        Returns:
            subprocess.CompletedProcess: The result of the executed command.

        Raises:
            subprocess.CalledProcessError: If the command fails and check is True.
        """

        try:
            result = subprocess.run(
                command,
                shell=shell,
                capture_output=capture_output,
                check=check,
                text=True,
                cwd=cwd,
                env=env
            )
            if capture_output:
                self.logger.debug(f"Command stdout: {result.stdout}")
                self.logger.debug(f"Command stderr: {result.stderr}")
            self.logger.info("Command executed successfully.")
            return result
        except subprocess.CalledProcessError as e:
            self.logger.info("Command executed failed.")
            self.logger.error(f"Error executing command: {e}")
            if capture_output:
                self.logger.error(f"Command stdout: {e.stdout}")
                self.logger.error(f"Command stderr: {e.stderr}")
            raise

    def get_sumo_tools_path(self):
        """
        Get the path to the SUMO tools directory.

        Returns:
            str: Path to the SUMO tools directory.
        """
        sumo_home = os.environ.get('SUMO_HOME')
        if sumo_home is None:
            raise EnvironmentError("SUMO_HOME environment variable not set.")
        return os.path.join(sumo_home, 'tools') 