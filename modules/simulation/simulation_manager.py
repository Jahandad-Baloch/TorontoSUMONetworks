# modules/simulation/simulation_manager.py
import os
from datetime import datetime
from modules.core.simulation_task import SimulationTask
from modules.core.network_base import NetworkBase

""" 
This script is used to manage the SUMO simulation.
path: scripts/simulation/simulation_manager.py
"""

class SimulationManager(NetworkBase, SimulationTask):
    """Manages SUMO simulation execution.

    Args:
        app_context (AppContext): Central application context.
    """
    def __init__(self, app_context) -> None:
        super().__init__(app_context)
        self.setup_output_dir()

    def setup_output_dir(self) -> None:
        """Set up the simulation output directories."""
        self.time_stamp = datetime.now().strftime("%m-%d_%H-%M")
        self.output_prefix = self.time_stamp
        self.summary_file = os.path.join(self.simulation_outputs, f"summary_output_{self.output_prefix}.xml")
        self.emission_file = os.path.join(self.simulation_outputs, f"emission_output_{self.output_prefix}.xml")
        self.queue_file = os.path.join(self.simulation_outputs, f"queue_output_{self.output_prefix}.xml")
        self.full_output_file = os.path.join(self.simulation_outputs, f"full_output_{self.output_prefix}.xml")

    def get_simulation_command(self) -> list:
        """Constructs the simulation command.

        Returns:
            list: The command list.
        """
        sumo_cmd = [
            "sumo", "-c", str(self.sumo_cfg_file)
        ]
        if self.simulation_settings['use_gui']:
            sumo_cmd[0] = sumo_cmd[0] + "-gui"
        if self.simulation_settings['save_output']:
            sumo_cmd = self._extend_output_options(sumo_cmd)
        return sumo_cmd

    def _extend_output_options(self, sumo_cmd: list) -> list:
        """Extends the command with output options.

        Args:
            sumo_cmd (list): Base simulation command.

        Returns:
            list: Command extended with output settings.
        """
        if self.simulation_settings['summary_output']:
            sumo_cmd.extend(["--summary-output", str(self.summary_file)])
        if self.simulation_settings['queue_output']:
            sumo_cmd.extend(["--queue-output", self.queue_file])
        if self.simulation_settings['emission_output']:
            sumo_cmd.extend(["--emission-output", self.emission_file])
        if self.simulation_settings['full_output']:
            sumo_cmd.extend(["--full-output", self.full_output_file])
        # when adding any output option, also add duration-log option
        sumo_cmd.extend(["--duration-log.statistics", "true"])
        return sumo_cmd

    def execute_simulation(self) -> None:
        """Executes the SUMO simulation."""
        self.logger.info("Simulation Execution Started.")
        command = self.get_simulation_command()
        self.logger.info(f"Executing command: {' '.join(command) if isinstance(command, list) else command}")
        self.executor.run_command(command)
        self.logger.info("Simulation Execution Ended.")
        self.logger.info(f"\n.......................\n")

    def execute(self) -> None:
        """Task entry-point: executes the simulation."""
        self.execute_simulation()
