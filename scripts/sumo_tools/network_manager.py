import os
from scripts.common.network_base import NetworkBase
from scripts.common.turn_counts_parser import TurningMovementsParser

""" 
This script is used to manage the SUMO network.
path: scripts/simulation/network_manager.py
"""


class SUMONetManager(NetworkBase):
    def __init__(self, config_file: str):
        """
        Initialize the SUMO network manager.

        Args:
            config_path (str): Path to the configuration file.
        """
        super().__init__(config_file)
        self.prepare_directories()


    def setup_files(self):
        """Prepare the paths for the routing files."""


        self.edge_types_file = os.path.join(self.network_outputs, f"{self.network_name}_edge_types.typ.xml")
        self.vtype_output_file = os.path.join(self.network_outputs, f"{self.network_name}_vtype.rou.xml")
        self.output_route_file = os.path.join(self.network_outputs, f"{self.network_name}_routes.rou.xml")

        self.output_trips_file = os.path.join(self.processing_outputs, f"{self.network_name}.trips.xml")
        self.initial_route_file = os.path.join(self.processing_outputs, f"initial_route_file.rou.xml")
        self.turn_counts_file = os.path.join(self.processing_outputs, f"turning_movements.xml")

        self.gtfs_file = os.path.join(self.paths['raw_data'], 'ttc-routes-and-schedules', [f for f in os.listdir(os.path.join(self.paths['raw_data'], 'ttc-routes-and-schedules')) if f.endswith('.zip')][0])
        self.bus_routes_file = os.path.join(self.network_outputs, f"{self.network_name}_public_transport.rou.xml")
        self.bus_vtype_file = os.path.join(self.network_outputs, f"{self.network_name}_public_transport_vtype.rou.xml")
        self.bus_routes_additional = os.path.join(self.network_outputs, f"{self.network_name}_gtfs_stops_routes.add.xml")

    def get_random_trips_command(self):
        """Get the random trips generation command."""
        random_trips_settings = self.config['random_trips']
        sumo_tool = os.path.join(self.sumo_tools_path, 'randomTrips.py')
        random_trips_cmd = [
            "python", sumo_tool,
            "-n", str(self.net_file),
            "-o", str(self.output_trips_file),
            "-r", str(self.initial_route_file),
            "--vtype-output", str(self.vtype_output_file),
            "--vehicle-class", "passenger",
            "-b", str(random_trips_settings['begin']),
            "-e", str(random_trips_settings['end'])
        ]

        if random_trips_settings.get('validate'):
            random_trips_cmd.append("--validate")
        if random_trips_settings['use_weights']:
            weight_prefix = os.path.join(self.network_outputs, self.network_name)
            random_trips_cmd.extend(["--weights-prefix", weight_prefix])
        if 'period' in random_trips_settings:
            random_trips_cmd.extend(["--period", str(random_trips_settings['period'])])

        return random_trips_cmd

    def get_generate_routes_command(self):
        """Get the generate routes command."""
        route_settings = self.config['route_sampler']
        input_route_file = self.initial_route_file
        sumo_tool = os.path.join(self.sumo_tools_path, 'routeSampler.py')
        generate_routes_cmd = [
            "python", sumo_tool,
            "-o", str(self.output_route_file),
            "-r", str(input_route_file),
            "-b", str(route_settings['begin']),
            "-e", str(route_settings['end'])
        ]

        if route_settings['use_count']:
            interval_counts, total_count = TurningMovementsParser.parse_turn_counts(self.turn_counts_file)
            total_count = int(total_count * route_settings['count_scale'])
            generate_routes_cmd.extend(["--total-count", str(total_count)])
        if route_settings['use_turn_movement_counts']:
            generate_routes_cmd.extend(["-t", str(self.turn_counts_file)])
        if route_settings['use_weights']:
            generate_routes_cmd.append("--weighted")

        return generate_routes_cmd

    def get_gtfs_import_command(self):
        """Get the GTFS import command."""
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

        return gtfs_import_cmd

    def execute_commands(self):
        """Prepare the commands to be executed and execute them."""
        self.setup_files()

        if self.routing_settings['generate_random_trips']:
            command = self.get_random_trips_command()
            self.logger.info(f"Executing command: {' '.join(command) if isinstance(command, list) else command}")
            self.executor.run_command(command)

        if self.routing_settings['sample_routes']:
            command = self.get_generate_routes_command()
            self.logger.info(f"Executing command: {' '.join(command) if isinstance(command, list) else command}")
            self.executor.run_command(command)

        if self.routing_settings['process_gtfs']:
            command = self.get_gtfs_import_command()
            self.logger.info(f"Executing command: {' '.join(command) if isinstance(command, list) else command}")
            self.executor.run_command(command)

        self.logger.info("Routing Command Executions Completed.")
        self.logger.info(f"\n.......................\n")

if __name__ == "__main__":
    manager = SUMONetManager('configurations/main_config.yaml')
    manager.execute_commands()
