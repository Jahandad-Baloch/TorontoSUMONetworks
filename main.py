import sys
import os
import argparse

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from scripts.common.utils import ConfigLoader, LoggerSetup
from scripts.fetch_data.fetch_toronto_data import TorontoDataFetcher
from scripts.traffic_data_processing.traffic_data_integrator import TrafficDataIntegrator
from scripts.build_sumo_net.build_network import SUMONetworkBuilder
from scripts.sumo_tools.detector_generator import DetectorGenerator
from scripts.sumo_tools.network_manager import SUMONetManager
from scripts.simulation.sumocfg_composer import SumoConfigComposer
from scripts.simulation.simulation_manager import SimulationManager
from scripts.results_analysis.results_analyzer import ResultsAnalyzer


""" 
This script is the main entry point for processing the SUMO network data.
path: main.py
"""

def main():
    """ 
    Main function to process the SUMO network data.
    """
    parser = argparse.ArgumentParser(description='Process SUMO network data.')
    parser.add_argument('--config', type=str, default='configurations/main_config.yaml', help='Path to the configuration file.')
    args = parser.parse_args()

    # Load the configuration
    configurations = args.config

    config = ConfigLoader.load_config(configurations)
    logger = LoggerSetup.setup_logger('main', config['logging']['log_dir'], config['logging']['log_level'])
    execution_settings = config[config['execution_settings']]

    print("Executing main...")

    # Fetch Toronto data
    if execution_settings['fetch_data']:
        print("Fetching data...")
        logger.info("Fetching data...")
        fetcher = TorontoDataFetcher(configurations)
        fetcher.fetch_datasets()
        logger.info("Specified data fetched.")

    # Build the SUMO network
    if execution_settings['build_network']:
        print("Building network...")
        logger.info("Building network...")
        network_builder = SUMONetworkBuilder(configurations)
        network_builder.build_network()
        logger.info("End of network building process.")

    # Process the traffic data
    if execution_settings['process_traffic_data']:
        print("Processing traffic data...")
        logger.info("Processing traffic data...")
        processor = TrafficDataIntegrator(configurations)
        processor.integrate_data()
        logger.info("End of traffic data processing.")

    # Generate routes
    if execution_settings['generate_routes']:
        print("Generating routes...")
        logger.info("Generating routes...")
        net_manager = SUMONetManager(configurations)
        net_manager.execute_commands()
        logger.info("End of routes generataion process.")

    # Generate detectors
    if execution_settings['build_detectors']:
        print("Generating detectors...")
        logger.info("Generating detectors...")
        detector_generator = DetectorGenerator(configurations)
        detector_generator.execute_detector_generation()
        logger.info("End of detector generation process.")

    # Compose the SUMO configuration file
    if execution_settings['compose_sumocfg']:
        print("Composing SUMO configuration file...")
        logger.info("Composing SUMO configuration file...")
        composer = SumoConfigComposer(configurations)
        composer.compose_sumo_config()
        logger.info("SUMO configuration file composed.")
        
    # Execute the SUMO simulation
    if execution_settings['run_simulation']:
        print("Running simulation...")
        logger.info("Running simulation...")
        simulation_manager = SimulationManager(configurations)
        simulation_manager.execute_simulation()
        logger.info("Simulation exectuion ended.")

    # Analyze the simulation results
    if execution_settings['analyze_results']:
        print("Analyzing results...")
        logger.info("Analyzing results...")
        analyzer = ResultsAnalyzer(configurations)
        analyzer.analyze_results()
        logger.info("Results analysis ended.")

    logger.info("End of Main().")
    logger.info(f"\n.......................\n")

    print("End of processing.")

if __name__ == '__main__':
    main()