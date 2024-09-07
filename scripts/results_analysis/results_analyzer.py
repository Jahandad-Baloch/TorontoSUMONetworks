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
        self.get_output_files()


    def get_output_files(self):
        """Get the paths to the output files."""
        self.summary_file = self.get_latest_file(self.simulation_outputs, 'summary_output')
        self.emission_file = self.get_latest_file(self.simulation_outputs, 'emission_output')
        self.queue_file = self.get_latest_file(self.simulation_outputs, 'queue_output')
        self.full_output_file = self.get_latest_file(self.simulation_outputs, 'full_output')
        self.stopsinfos_file = self.get_latest_file(self.simulation_outputs, 'stops_infos')
        
    def get_latest_file(self, directory, file_prefix):
        """Get the latest file in the directory."""
        files = os.listdir(directory)
        files = [file for file in files if file.startswith(file_prefix)]
        files.sort()
        if files:
            return os.path.join(directory, files[-1])

    def setup_tools(self):
        """
        Setup the tools for results analysis.
        """

        self.logger.info("Setting up tools for results analysis.")
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
        summary_file_output = os.path.join(self.simulation_outputs, 'summary_file.png')

        summary_cmd = [
            "python", self.summary_plotter, "-i", self.summary_file, "-o", summary_file_output,
            "-m", "halting", "--xlim", "28800,34200", "--ylim", "0,200", "--xlabel", "time", 
            "--ylabel", "halting_vehicles", "--title", "halting vehicles over time"
        ]

        return summary_cmd

    
    def get_emission_command(self):
        """Get the emission command."""
        emission_output = os.path.join(self.simulation_outputs, 'emission.png')

        emission_cmd = [
            "python", self.xml_plotter, self.emission_file, "-o", emission_output,
            "--xattr", "time", "--yattr", "CO2", "--xlabel", "time", "--ylabel", "CO2",
            "--title", "CO2 emissions over time", "--xtime1"
        ]

        return emission_cmd

    def get_queue_command(self):
        """Get the queue command."""
        queue_output = os.path.join(self.simulation_outputs, 'queue.png')

        queue_cmd = [
            "python", self.xml_plotter, self.queue_file, "-i", "queueing_time",
            "--filter-ids", "1138214_0", "-x", "timestep", "-y", "queueing_time", "-o", queue_output
        ]
        return queue_cmd

    def get_stop_infos_command(self):
        """Get the stop infos command."""
        stop_infos_cmd = [
            "python", self.xml_plotter, self.stopsinfos_file, 
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
            print("Getting queue command")
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
            if type(command) == list:
                self.logger.info(f"Running command: {' '.join(command)}")
            elif type(command) == str:
                self.logger.info(f"Running command: {command}")
            self.executor.run_command(command)
            
        self.logger.info("Results Analysis Ended.")
        self.logger.info(f"\n.......................\n")
        
if __name__ == "__main__":
    analyzer = ResultsAnalyzer('configurations/main_config.yaml')
    analyzer.analyze_results()