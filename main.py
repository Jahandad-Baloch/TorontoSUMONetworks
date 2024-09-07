import sys
import os
import argparse

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from scripts.common.utils import ConfigLoader, LoggerSetup
from scripts.fetch_data.fetch_toronto_data import TorontoDataFetcher
from scripts.traffic_data_processing.main_processor import MainProcessor
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

    # Fetch Toronto data
    if config['execution_settings']['fetch_data']:
        logger.info("Fetching data...")
        fetcher = TorontoDataFetcher(configurations)
        fetcher.fetch_datasets()
        logger.info("Specified data fetched.")

    # Build the SUMO network
    if config['execution_settings']['build_network']:
        logger.info("Building network...")
        network_builder = SUMONetworkBuilder(configurations)
        network_builder.build_network()
        logger.info("End of network building process.")

    # Process the traffic data
    if config['execution_settings']['process_traffic_data']:
        logger.info("Processing traffic data...")
        processor = MainProcessor(configurations)
        processor.process_network()
        logger.info("End of traffic data processing.")

    # Generate routes
    if config['execution_settings']['generate_routes']:
        logger.info("Generating routes...")
        net_manager = SUMONetManager(configurations)
        net_manager.execute_commands()
        logger.info("End of routes generataion process.")

    # Generate detectors
    if config['execution_settings']['build_detectors']:
        logger.info("Generating detectors...")
        detector_generator = DetectorGenerator(configurations)
        detector_generator.execute_detector_generation()
        logger.info("End of detector generation process.")

    # Compose the SUMO configuration file
    if config['execution_settings']['compose_sumocfg']:
        logger.info("Composing SUMO configuration file...")
        composer = SumoConfigComposer(configurations)
        composer.compose_sumo_config()
        logger.info("SUMO configuration file composed.")
        
    # Execute the SUMO simulation
    if config['execution_settings']['run_simulation']:
        logger.info("Running simulation...")
        simulation_manager = SimulationManager(configurations)
        simulation_manager.execute_simulation()
        logger.info("Simulation exectuion ended.")

    # Analyze the simulation results
    if config['execution_settings']['analyze_results']:
        logger.info("Analyzing results...")
        analyzer = ResultsAnalyzer(configurations)
        analyzer.analyze_results()
        logger.info("Results analysis ended.")

    logger.info("End of Main().")
    logger.info(f"\n.......................\n")


if __name__ == '__main__':
    main()