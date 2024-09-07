import os
from scripts.common.network_base import NetworkBase
from datetime import datetime

""" 
This script is used to manage the SUMO simulation.
path: scripts/simulation/simulation_manager.py
"""

class SimulationManager(NetworkBase):
    def __init__(self, config_file: str):
        """
        Initialize the simulation executer.

        Args:
            config_path (str): Path to the configuration file.
        """
        super().__init__(config_file)
        self.prepare_directories()
        self.setup_output_dir()

    def setup_output_dir(self):
        """Setup the output directories."""
        self.time_stamp = datetime.now().strftime("%m-%d_%H-%M")
        self.output_prefix = self.time_stamp
        self.summary_file = os.path.join(self.simulation_outputs, f"summary_output_{self.output_prefix}.xml")
        self.emission_file = os.path.join(self.simulation_outputs, f"emission_output_{self.output_prefix}.xml")
        self.queue_file = os.path.join(self.simulation_outputs, f"queue_output_{self.output_prefix}.xml")
        self.full_output_file = os.path.join(self.simulation_outputs, f"full_output_{self.output_prefix}.xml")

    def get_simulation_command(self):
        """Get the simulation command."""
        sumo_cmd = [
            "sumo", "-c", str(self.sumo_cfg_file)
        ]

        if self.simulation_settings['use_gui']:
            sumo_cmd[0] = sumo_cmd[0] + "-gui"

        if self.simulation_settings['save_output']:
            sumo_cmd = self._extend_output_options(sumo_cmd)
            
        return sumo_cmd

    def _extend_output_options(self, sumo_cmd):
        """Extend the output options for the SUMO command."""

        if self.simulation_settings['summary_output']:
            sumo_cmd.extend(["--summary-output", str(self.summary_file)])

        if self.simulation_settings['queue_output']:
            sumo_cmd.extend(["--queue-output", self.queue_file])
            
        if self.simulation_settings['emission_output']:
            sumo_cmd.extend(["--emission-output", self.emission_file])

        if self.simulation_settings['full_output']:
            sumo_cmd.extend(["--full-output", self.full_output_file])
            
        return sumo_cmd


    def execute_simulation(self):
        """Execute the SUMO simulation."""
        self.logger.info("Simulation Execution Started.")
        command = self.get_simulation_command()
        self.logger.info(f"Executing command: {' '.join(command) if isinstance(command, list) else command}")
        self.executor.run_command(command)
        self.logger.info("Simulation Execution Ended.")
        self.logger.info(f"\n.......................\n")
        
if __name__ == "__main__":
    simulation_manager = SimulationManager('configurations/main_config.yaml')
    simulation_manager.execute_simulation()
