import os
from scripts.common.network_base import NetworkBase

"""
This script is used to analyze the simulation results.
path: scripts/results_analysis/results_analyzer.py
"""

class ResultsAnalyzer(NetworkBase):
    def __init__(self, config_file: str):
        """
        Initializes the ResultsAnalyzer.

        Args:
            config_file (str): Path to the configuration file.
        """
        super().__init__(config_file)
        self.prepare_directories()


    def setup_tools(self):
        """
        Setup the tools for results analysis.
        """

        self.logger.info("Setting up tools for results analysis.")
        self.output_prefix = self.config['simulation_settings']['output_prefix']
        self.visualization_dir = os.path.join(self.sumo_tools_path, "visualization")

        # Get the paths to the tools
        self.trajectories_plotter = os.path.join(self.sumo_tools_path, "plot_trajectories.py")
        self.xml_plotter = os.path.join(self.visualization_dir, "plotXMLAttributes.py")
        self.net_dump_plotter = os.path.join(self.visualization_dir, "plot_net_dump.py")
        self.speed_plotter = os.path.join(self.visualization_dir, "plot_speeds.py")
        self.tls_plotter = os.path.join(self.visualization_dir, "plot_net_trafficLights.py")
        self.summary_plotter = os.path.join(self.visualization_dir, "plot_summary.py")

        self.logger.info("Tools setup completed.")


    def get_summary_command(self):
        """Get the stop infos command."""
        summary_file = os.path.join(self.simulation_outputs, f"summary_output_{self.timestamp}.xml")
        summary_file_output = os.path.join(self.simulation_outputs, 'summary_file.png')

        summary_cmd = [
            "python", self.summary_plotter, "-i", summary_file, "-o", summary_file_output,
            "-m", "halting", "--xlim", "28800,34200", "--ylim", "0,200", "--xlabel", "time", 
            "--ylabel", "halting_vehicles", "--title", "halting vehicles over time"
        ]

        return summary_cmd

    
    def get_emission_command(self):
        """Get the emission command."""
        emission_file = os.path.join(self.simulation_outputs, f"emission_output_{self.timestamp}.xml")
        emission_output = os.path.join(self.simulation_outputs, 'emission.png')

        emission_cmd = [
            "python", self.xml_plotter, emission_file, "-o", emission_output,
            "--xattr", "time", "--yattr", "CO2", "--xlabel", "time", "--ylabel", "CO2",
            "--title", "CO2 emissions over time", "--xtime1"
        ]

        return emission_cmd
    
    def get_queue_command(self):
        """Get the queue command."""
        queue_file = os.path.join(self.simulation_outputs, f"queue_output_{self.timestamp}.xml")
        queue_output = os.path.join(self.simulation_outputs, 'queue.png')

        queue_cmd = [
            "python", self.xml_plotter, queue_file, "-i", "queueing_time",
            "--filter-ids", "1138214_0", "-x", "timestep", "-y", "queueing_time", "-o", queue_output
        ]
        return queue_cmd



    def get_stop_infos_command(self):
        """Get the stop infos command."""
        stopsinfos_file = os.path.join(self.simulation_outputs, f"stopinfos_{self.timestamp}.xml")

        stop_infos_cmd = [
            "python", self.xml_plotter, stopsinfos_file, 
            "busStop", "-x", "loadedPersons", "-y", "delay", "--scatterplot", "--legend"
        ]

        return stop_infos_cmd

    def get_route_command(self):
        """Get the route command."""

        route_file = os.path.join(self.network_outputs, f"{self.network_name}_routes.rou.xml")
        stoplist_file = os.path.join(self.processing_outputs, 'stoplist.txt')

        route_cmd = [
            "python", self.xml_plotter, route_file, "-i", "busStop",
            "-x", "loadedPersons" "-y", "delay", "--ytime1", "--legend", "--xticks-file", stoplist_file, "--invert-yaxis", "--marker", "o"
        ]
        
        return route_cmd
    
    def get_turn_counts_command(self):
        """Get the turn counts command."""

        turn_counts_file = os.path.join(self.processing_outputs, 'turning_movements.xml')

        turn_counts_cmd = [
            "python", self.xml_plotter, turn_counts_file,
            "-i", "count", "-x", "begin", "-y", "count", "--xtime0", "--legend"
        ]

        return turn_counts_cmd

    
    def get_speed_command(self):
        """Plot the speeds."""
        
        speeds_output = os.path.join(self.simulation_outputs, 'speeds.png')

        plot_speeds_cmd = [
            "python", self.net_dump_plotter, "-n", self.net_file, "-o", speeds_output
        ]

        return plot_speeds_cmd


    def get_commands(self):
        """Analyze the simulation results."""
        self.logger.info("Results Analysis Started.")
        commands_to_run = []

        if self.config['analysis_settings']['analyze_stop_infos']:
            # get the command and add it to the list of commands to run
            commands_to_run.append(self.get_stop_infos_command())

        if self.config['analysis_settings']['analyze_queue']:
            commands_to_run.append(self.get_queue_command())
            
        if self.config['analysis_settings']['analyze_route']:
            commands_to_run.append(self.get_route_command())
            
        if self.config['analysis_settings']['analyze_turn_counts']:
            commands_to_run.append(self.get_turn_counts_command())
            
        if self.config['analysis_settings']['analyze_speed']:
            commands_to_run.append(self.get_speed_command())
            
        if self.config['analysis_settings']['analyze_summary']:
            commands_to_run.append(self.get_summary_command())
        
        if self.config['analysis_settings']['analyze_emission']:
            commands_to_run.append(self.get_emission_command())
        
        return commands_to_run

    def analyze_results(self):
        """Analyze the simulation results."""
        self.setup_tools()
        commands_to_run = self.get_commands()

        self.logger.info("Results Analysis Started.")
        for command in commands_to_run:
            self.logger.info(f"Running command: {' '.join(command)}")
            self.executor.run_command(command)
            
        self.logger.info("Results Analysis Ended.")
        self.logger.info(f"\n.......................\n")
        
if __name__ == "__main__":
    analyzer = ResultsAnalyzer('configurations/main_config.yaml')
    analyzer.analyze_results()