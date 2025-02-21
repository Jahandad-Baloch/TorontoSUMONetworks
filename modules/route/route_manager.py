# modules/route/route_manager.py
import os
from modules.core.simulation_task import SimulationTask
from modules.core.network_base import NetworkBase
from modules.common.turning_movements_parser import TurningMovementsParser

""" 
This script is used to manage the SUMO network.
path: scripts/simulation/route_manager.py
"""


class SumoRouteManager(NetworkBase, SimulationTask):
    """Manages the SUMO network routing tasks.

    Args:
        app_context (AppContext): Central application context.
    """

    def __init__(self, app_context) -> None:
        """
        Initialize the SUMO network manager.

        Args:
            app_context (AppContext): Central application context.
        """
        super().__init__(app_context)

    def get_random_trips_command(self, mode: str) -> list:
        """Returns the random trips generation command.

        Args:
            mode (str): The vehicle mode.

        Returns:
            list: The assembled command.
        """
        files = self.files_by_mode[mode]
        mode_vclass = {'cars': 'passenger', 'truck': 'truck', 'bus': 'public_transport', 'bike': 'bicycle', 'peds': 'pedestrian'}
        random_trips_settings = self.config['random_trips']
        sumo_tool = os.path.join(self.sumo_tools_path, 'randomTrips.py')
        random_trips_cmd = [
            "python", sumo_tool,
            "-n", str(self.net_file),
            "-o", str(files['output_trips_file']),
            "-r", str(files['initial_route_file']),
            "--vtype-output", str(files['vtype_output_file']),
            "--vehicle-class", mode_vclass[mode],
            "-b", str(random_trips_settings['begin']),
            "-e", str(random_trips_settings['end'])
        ]
        if mode == 'peds':
            random_trips_cmd.append('--pedestrians')
        if random_trips_settings.get('validate'):
            random_trips_cmd.append("--validate")
        if random_trips_settings['use_weights']:
            weight_prefix = os.path.join(self.network_outputs, self.network_name)
            random_trips_cmd.extend(["--weights-prefix", weight_prefix])
        if 'period' in random_trips_settings:
            random_trips_cmd.extend(["--period", str(random_trips_settings['period'])])

        self.logger.info(f"Random Trips Command: {' '.join(random_trips_cmd)}")
        return random_trips_cmd

    def get_generate_routes_command(self, mode: str) -> list:
        """Returns the generate routes command.

        Args:
            mode (str): The vehicle mode.

        Returns:
            list: The assembled command.
        """
        route_settings = self.config['route_sampler']
        files = self.files_by_mode[mode]
        sumo_tool = os.path.join(self.sumo_tools_path, 'routeSampler.py')
        generate_routes_cmd = [
            "python", sumo_tool,
            "-o", str(files['output_route_file']),
            "-r", str(files['initial_route_file']),
            "-b", str(route_settings['begin']),
            "-e", str(route_settings['end']),
            "--prefix", str(mode)
        ]
        if mode == 'peds':
            generate_routes_cmd.append('--pedestrians')
            generate_routes_cmd.append('--allow-fringe')
            generate_routes_cmd.append('--verbose')
        elif mode in ['cars', 'truck']:
            if route_settings['use_turn_movement_counts']:
                interval_counts, total_count = TurningMovementsParser.parse_turn_counts(files['turn_counts_file'])
                total_count = int(total_count * route_settings['count_scale'])
                generate_routes_cmd.extend(["--total-count", str(total_count)])
                generate_routes_cmd.extend(["-t", str(files['turn_counts_file'])])
            if route_settings['use_weights']:
                generate_routes_cmd.append("--weighted")
            
        self.logger.info(f"Generate Routes Command: {' '.join(generate_routes_cmd)}")
        return generate_routes_cmd

    def get_gtfs_import_command(self) -> list:
        """Returns the GTFS import command.

        Returns:
            list: The assembled command.
        """
        gtfs_settings = self.config['gtfs_import']
        sumo_tool = os.path.join(self.sumo_tools_path, 'import', 'gtfs', 'gtfs2pt.py')
        gtfs_import_cmd = [
            "python", sumo_tool,
            "--gtfs", str(self.gtfs_file),
            "-n", str(self.net_file),
            "--route-output", str(self.bus_routes_file),
            "--additional-output", str(self.bus_routes_additional),
            "--vtype-output", str(self.bus_vtype_file),
            "--modes", str(gtfs_settings.get('modes', 'bus')),
            "--date", str(gtfs_settings.get('date', '20240813')),
            "-b", str(gtfs_settings['begin']),
            "-e", str(gtfs_settings['end'])
        ]
        self.logger.info(f"GTFS Import Command: {' '.join(gtfs_import_cmd)}")
        return gtfs_import_cmd

    def execute_commands(self) -> None:
        """Executes the routing commands."""
        for mode in self.modes:
            if self.routing_settings['generate_random_trips']:
                cmd = self.get_random_trips_command(mode)
                self.executor.run_command(cmd)
            if self.routing_settings['sample_routes']:
                cmd = self.get_generate_routes_command(mode)
                self.executor.run_command(cmd)
        if self.routing_settings['process_gtfs']:
            cmd = self.get_gtfs_import_command()
            self.executor.run_command(cmd)
        self.logger.info("Routing Command Executions Completed.")

    def execute(self) -> None:
        """Task entry-point: executes the route manager commands."""
        self.execute_commands()
