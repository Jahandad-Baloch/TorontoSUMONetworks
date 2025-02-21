# This module is responsible for analyzing simulation results by processing output XML files and generating visualizations.
# Path: modules/simulation/results_analyzer.py

import os
from pathlib import Path
from modules.core.simulation_task import SimulationTask
from modules.common.command_executor import CommandExecutor

class ResultsAnalyzer(SimulationTask):
    """Analyzes simulation results by processing output XML files and generating visualizations.

    This task sets up required tools and runs various analysis commands (e.g., for summary,
    emissions, queue, etc.) based on configuration settings.
    """

    # def __init__(self, app_context: AppContext) -> None:
    def __init__(self, app_context) -> None:
        """
        Initializes the ResultsAnalyzer task.

        Args:
            app_context (AppContext): Shared application context containing configuration and logger.
        """
        super().__init__(app_context)
        self.executor = CommandExecutor(logger=self.logger)
        # self.setup_paths(self.simulation_outputs, "summary_output")
        
        self.app_context = app_context
        self.config = app_context.config
        self.logger = app_context.logger
        # Update: use new network configuration key
        self.network_config = self.config['network']
        # Optionally, if needed, derive network name from network_config
        self.network_area = self.network_config['area'].get(self.network_config['extent'], 'default_area')
        self.network_name = self.network_area.replace(' ', '_').lower()

    def setup_paths(self, directory: Path, file_prefix: str) -> None:
        """
        Sets up file paths for simulation outputs and related directories.
        """
        sim_data = self.config['paths'].get('simulation_output', '')
        net_area = self.network_name
        self.simulation_outputs = Path(sim_data) / net_area
        """
        Returns the latest file in the directory that starts with the given prefix.

        Args:
            directory (Path): Directory in which to search.
            file_prefix (str): File prefix to filter by.

        Returns:
            str: Full path to the latest file, or an empty string if none is found.
        """
        files = sorted([f for f in os.listdir(directory) if f.startswith(file_prefix)])
        if files:
            return str(directory / files[-1])
        return ""

    def setup_tools(self) -> None:
        """
        Sets up the paths to external tools for result analysis.
        """
        self.logger.info("Setting up tools for results analysis.")

        # Get the path to the SUMO tools directory
        sumo_tools = Path(self.config['paths'].get('sumo_tools', ''))

        # Get the paths to the SUMO plot and visualization tools
        self.trajectories_plotter = sumo_tools / "plot_trajectories.py"
        self.screen_shot_creator = sumo_tools / "createScreenshotSequence.py"
        self.visualization_dir = sumo_tools / "visualization"
        self.xml_plotter = self.visualization_dir / "plotXMLAttributes.py"
        self.net_dump_plotter = self.visualization_dir / "plot_net_dump.py"
        self.speed_plotter = self.visualization_dir / "plot_speeds.py"
        self.tls_plotter = self.visualization_dir / "plot_net_trafficLights.py"
        self.summary_plotter = self.visualization_dir / "plot_summary.py"
        self.logger.info("Tools setup completed.")

    def get_summary_command(self) -> list[str]:
        """
        Constructs the command for generating summary visualization.

        Returns:
            list[str]: Command arguments for summary visualization.
        """
        summary_output = str(self.simulation_outputs / 'summary_file.png')
        command = [
            "python", str(self.summary_plotter),
            "-i", self.summary_file,
            "-o", summary_output,
            "-m", "halting",
            "--xlim", "28800,34200",
            "--ylim", "0,200",
            "--xlabel", "time",
            "--ylabel", "halting_vehicles",
            "--title", "Halting Vehicles Over Time"
        ]
        return command

    def get_emission_command(self) -> list[str]:
        """
        Constructs the command for generating emission visualization.

        Returns:
            list[str]: Command arguments for emission visualization.
        """
        emission_output = str(self.simulation_outputs / 'emission.png')
        command = [
            "python", str(self.xml_plotter), self.emission_file,
            "-o", emission_output,
            "--xattr", "time", "--yattr", "CO2",
            "--xlabel", "time", "--ylabel", "CO2",
            "--title", "CO2 Emissions Over Time"
        ]
        return command

    def get_queue_command(self) -> list[str]:
        """
        Constructs the command for generating queue visualization.

        Returns:
            list[str]: Command arguments for queue visualization.
        """
        queue_output = str(self.simulation_outputs / 'queue.png')
        command = [
            "python", str(self.xml_plotter), self.queue_file,
            "-i", "queueing_time",
            "--filter-ids", "1138214_0",
            "-x", "timestep", "-y", "queueing_time",
            "-o", queue_output
        ]
        return command

    def get_stop_infos_command(self) -> list[str]:
        """
        Constructs the command for generating stop information visualization.

        Returns:
            list[str]: Command arguments for stop information visualization.
        """
        command = [
            "python", str(self.xml_plotter), self.stopsinfos_file,
            "busStop", "-x", "loadedPersons", "-y", "delay",
            "--scatterplot", "--legend"
        ]
        return command

    def get_route_command(self) -> list[str]:
        """
        Constructs the command for generating route visualization.

        Returns:
            list[str]: Command arguments for route visualization.
        """
        net_area = self.config['network_settings']['network_area'].replace(' ', '_').lower()
        route_file = os.path.join(self.config['paths']['network_data'], f"{net_area}_routes.rou.xml")
        stoplist_file = str(self.simulation_outputs / 'stoplist.txt')
        command = [
            "python", str(self.xml_plotter), route_file,
            "-i", "busStop",
            "-x", "loadedPersons", "-y", "delay",
            "--ytime1", "--legend",
            "--xticks-file", stoplist_file,
            "--invert-yaxis", "--marker", "o"
        ]
        return command

    def get_turn_counts_command(self) -> list[str]:
        """
        Constructs the command for generating turning counts visualization.

        Returns:
            list[str]: Command arguments for turning counts visualization.
        """
        turn_counts_file = str(self.simulation_outputs / 'turning_movements.xml')
        command = [
            "python", str(self.xml_plotter), turn_counts_file,
            "-i", "count", "-x", "begin", "-y", "count",
            "--xtime0", "--legend"
        ]
        return command

    def get_speed_command(self) -> list[str]:
        """
        Constructs the command for generating speed visualization.

        Returns:
            list[str]: Command arguments for speed visualization.
        """
        speeds_output = str(self.simulation_outputs / 'speeds.png')
        command = [
            "python", str(self.net_dump_plotter),
            "-n", self.config['paths'].get('net_file', ""),
            "-o", speeds_output
        ]
        return command

    def get_commands(self) -> list[list[str]]:
        """
        Compiles analysis commands based on configuration settings.

        Returns:
            list[list[str]]: A list of command argument lists.
        """
        self.logger.info("Compiling result analysis commands.")
        commands = []
        analysis_settings = self.config.get('analysis_settings', {})

        if analysis_settings.get('analyze_stop_infos', False):
            commands.append(self.get_stop_infos_command())
        if analysis_settings.get('analyze_queue', False):
            commands.append(self.get_queue_command())
        if analysis_settings.get('analyze_route', False):
            commands.append(self.get_route_command())
        if analysis_settings.get('analyze_turn_counts', False):
            commands.append(self.get_turn_counts_command())
        if analysis_settings.get('analyze_speed', False):
            commands.append(self.get_speed_command())
        if analysis_settings.get('analyze_summary', False):
            commands.append(self.get_summary_command())
        if analysis_settings.get('analyze_emission', False):
            commands.append(self.get_emission_command())

        return commands

    def analyze_results(self) -> None:
        """
        Executes all analysis commands to generate result visualizations.
        """
        self.setup_tools()
        commands = self.get_commands()
        self.logger.info("Starting results analysis.")
        for command in commands:
            self.logger.info(f"Running command: {' '.join(command)}")
            self.executor.run_command(command)
        self.logger.info("Results analysis completed.")

    def execute(self) -> None:
        """
        Executes the ResultsAnalyzer task.
        """
        self.analyze_results()


