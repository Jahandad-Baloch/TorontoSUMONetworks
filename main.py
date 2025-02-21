# main.py
import sys
import os

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

import argparse
from modules.core.app_context import AppContext
from modules.download.dataset_downloader import DatasetDownloader
from modules.network.traffic_network_creation import TrafficNetworkCreation
from modules.traffic.traffic_data_integrator import TrafficDataIntegrator
from modules.route import SumoRouteManager, NetworkManager, DetectorGenerator
from modules.simulation.simulation_manager import SimulationManager
from modules.simulation.analysis_manager import AnalysisManager
from modules.common.snap_generator import SnapGenerator
from modules.simulation.sumocfg_composer import SumoConfigComposer
from modules.visualization.dashboard import DashboardApp

"""
Main entry point for processing the SUMO network data.

This script initializes the application context and executes the simulation tasks
based on configuration settings.
"""

def main() -> None:
    """
    Parses command line arguments, sets up the application context, and executes the
    simulation pipeline tasks.
    """
    parser = argparse.ArgumentParser(description='Process SUMO network data.')
    parser.add_argument('--config', type=str, default='configurations/main_config.yaml',
                        help='Path to the configuration file.')
    args = parser.parse_args()

    # Initialize application context
    app_context = AppContext(args.config)
    
    # Retrieve the execution settings using the active profile.
    profile = app_context.config['active_execution_profile']
    execution_settings = app_context.config['execution'][profile]
    
    # Define the pipeline: (TaskClass, configuration key)
    tasks = [
        (DatasetDownloader, 'fetch_data'),
        (TrafficNetworkCreation, 'build_network'),
        (SnapGenerator, 'generate_snapshots'),
        (TrafficDataIntegrator, 'integrate_traffic'),
        (SumoRouteManager, 'generate_routes'),
        (NetworkManager, 'prepare_network'),
        (DetectorGenerator, 'generate_detectors'),
        (SumoConfigComposer, 'compose_sumocfg'),
        (SimulationManager, 'run_simulation'),
        (AnalysisManager, 'analyze_results')
        (DashboardApp, 'run_dashboard')
    ]

    # Execute tasks based on configuration settings.
    for TaskClass, setting_key in tasks:
        if execution_settings.get(setting_key, False):
            try:
                task = TaskClass(app_context)
                print(f"Executing task: {TaskClass.__name__}")
                task.execute()
            except Exception as e:
                app_context.logger.error(f"Task {TaskClass.__name__} failed: {e}")
                break

if __name__ == '__main__':
    main()

