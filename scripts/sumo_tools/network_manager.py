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

    def get_random_trips_command(self, mode):
        """Get the random trips generation command."""
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

        if random_trips_settings.get('validate'):
            random_trips_cmd.append("--validate")
        if random_trips_settings['use_weights']:
            weight_prefix = os.path.join(self.network_outputs, self.network_name)
            random_trips_cmd.extend(["--weights-prefix", weight_prefix])
        if 'period' in random_trips_settings:
            random_trips_cmd.extend(["--period", str(random_trips_settings['period'])])

        self.logger.info(f"Random Trips Command: {' '.join(random_trips_cmd)}")

        return random_trips_cmd

    def get_generate_routes_command(self, mode):
        """Get the generate routes command."""
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


        if route_settings['use_turn_movement_counts']:
            interval_counts, total_count = TurningMovementsParser.parse_turn_counts(files['turn_counts_file'])
            total_count = int(total_count * route_settings['count_scale'])
            generate_routes_cmd.extend(["--total-count", str(total_count)])
            generate_routes_cmd.extend(["-t", str(files['turn_counts_file'])])
        if route_settings['use_weights']:
            generate_routes_cmd.append("--weighted")
            
        self.logger.info(f"Generate Routes Command: {' '.join(generate_routes_cmd)}")

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
        
        self.logger.info(f"GTFS Import Command: {' '.join(gtfs_import_cmd)}")

        return gtfs_import_cmd


    def execute_commands(self):
        """Execute the routing commands."""
        for mode in self.modes:
            if self.routing_settings['generate_random_trips']:
                random_trips_cmd = self.get_random_trips_command(mode)
                self.executor.run_command(random_trips_cmd)
                
            if self.routing_settings['sample_routes']:
                route_cmd = self.get_generate_routes_command(mode)
                self.executor.run_command(route_cmd)
                
        if self.routing_settings['process_gtfs']:
            gtfs_cmd = self.get_gtfs_import_command()
            self.executor.run_command(gtfs_cmd)

        self.logger.info("Routing Command Executions Completed.")
        self.logger.info(f"\n.......................\n")

if __name__ == "__main__":
    manager = SUMONetManager('configurations/main_config.yaml')
    manager.execute_commands()
