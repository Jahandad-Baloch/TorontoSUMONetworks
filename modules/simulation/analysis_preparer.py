# modules/simulation/analysis_preparer.py
import os
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional, List, Dict
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from modules.core.simulation_task import SimulationTask
from modules.core.network_base import NetworkBase
from modules.common.command_executor import CommandExecutor
from modules.core.app_context import AppContext

class AnalysisPreparer(NetworkBase, SimulationTask):
    """Analyzes SUMO simulation outputs and generates informative plots.

    This class loads various output XML files (summary, queue, emission, etc.),
    performs data aggregation, and produces multi-panel visualizations. In addition,
    it computes basic statistics and correlations that can be used to evaluate the
    performance of advanced traffic control techniques.
    """

    def __init__(self, app_context: AppContext) -> None:
        """
        Initializes the ResultsAnalyzer.

        Args:
            app_context (AppContext): Shared application context containing configuration and logger.
        """
        super().__init__(app_context)
        self.executor = CommandExecutor(logger=self.logger)

        self.app_context = app_context
        self.config = app_context.config
        self.logger = app_context.logger
        # Update: use new network configuration key
        self.network_config = self.config['network']
        # Optionally, if needed, derive network name from network_config
        self.network_area = self.network_config['area'].get(self.network_config['extent'], 'default_area')
        self.network_name = self.network_area.replace(' ', '_').lower()

        # Ensure simulation output directory exists
        self.simulation_outputs = Path(self.config['paths'].get('simulation_data', '.')) / \
                                  self.config['network']['area'].replace(' ', '_').lower()
        self.simulation_outputs = self.config['paths']['simulation_data']
        
        self.setup_input_files()
        
    # Function to set up the paths for queue, emission, summary, and full output files
    def setup_input_files(self) -> None:
        """
        Sets up the paths for input files used in result
        analysis.
        """
        self.logger.info("Setting up input files for results analysis.")
        self.output_dir = f"{self.simulation_outputs}/{self.network_name}"
        
        # Iteratre over the files inside the output directory
        for file in os.listdir(self.output_dir):
            # if queue
            if file.startswith("queue"):
                self.queue_file = f"{self.output_dir}/{file}"
            if file.startswith("emission"):
                self.emission_file = f"{self.output_dir}/{file}"
            if file.startswith("summary"):
                self.summary_file = f"{self.output_dir}/{file}"
            if file.startswith("full_output"):
                self.full_output_file = f"{self.output_dir}/{file}"
        self.logger.info("Input files setup completed.")

    def _parse_xml_to_dataframe(self, xml_file: Path, element_tag: str, attributes: List[str]) -> pd.DataFrame:
        """
        Parses an XML file into a Pandas DataFrame based on a specified element tag and its attributes.

        Args:
            xml_file (Path): Path to the XML file.
            element_tag (str): The XML element tag to parse.
            attributes (List[str]): List of attribute names to extract.

        Returns:
            pd.DataFrame: DataFrame with the extracted data.
        """
        try:
            tree = ET.parse(xml_file)
            root = tree.getroot()
            records = []
            for elem in root.findall(f".//{element_tag}"):
                record = {attr: float(elem.get(attr)) if elem.get(attr) and elem.get(attr).replace('.', '', 1).isdigit() 
                          else elem.get(attr) for attr in attributes}
                records.append(record)
            if records:
                return pd.DataFrame(records)
            else:
                self.logger.warning(f"No elements found for tag {element_tag} in {xml_file}")
                return pd.DataFrame()
        except Exception as e:
            self.logger.error(f"Error parsing XML file {xml_file}: {e}")
            return pd.DataFrame()

    def analyze_summary(self) -> pd.DataFrame:
        """
        Loads and returns a DataFrame from the summary output XML.

        Returns:
            pd.DataFrame: DataFrame containing summary data (e.g., halting vehicles over time).
        """
        if not self.summary_file:
            self.logger.error("Summary file not found.")
            return pd.DataFrame()
        # Assuming the XML elements are named 'interval' and have attributes like 'begin', 'end', 'halting'
        df = self._parse_xml_to_dataframe(self.summary_file, "interval", ["begin", "end", "halting"])
        if not df.empty:
            df["time_mid"] = (df["begin"] + df["end"]) / 2
        return df

    def analyze_queue(self) -> pd.DataFrame:
        """
        Loads and returns a DataFrame from the queue output XML.

        Returns:
            pd.DataFrame: DataFrame containing queue length data over time.
        """
        if not self.queue_file:
            self.logger.error("Queue file not found.")
            return pd.DataFrame()
        # Assuming the XML elements are named 'interval' with attributes 'timestep' and 'queueing_time'
        return self._parse_xml_to_dataframe(self.queue_file, "interval", ["timestep", "queueing_time"])

    def analyze_emission(self) -> pd.DataFrame:
        """
        Loads and returns a DataFrame from the emission output XML.

        Returns:
            pd.DataFrame: DataFrame containing emission data (e.g., CO2) over time.
        """
        if not self.emission_file:
            self.logger.error("Emission file not found.")
            return pd.DataFrame()
        # Assuming the XML elements are named 'interval' with attributes 'time' and 'CO2'
        return self._parse_xml_to_dataframe(self.emission_file, "interval", ["time", "CO2"])

    def plot_analysis(self) -> None:
        """
        Generates a multi-panel figure with the summary, queue, and emission analyses.
        """
        # Load data
        summary_df = self.analyze_summary()
        queue_df = self.analyze_queue()
        emission_df = self.analyze_emission()

        # Create a figure with subplots
        fig, axes = plt.subplots(nrows=3, ncols=1, figsize=(12, 15), sharex=True)

        # Summary Plot: Halting Vehicles over Time
        if not summary_df.empty:
            sns.lineplot(data=summary_df, x="time_mid", y="halting", ax=axes[0])
            axes[0].set_title("Halting Vehicles Over Time")
            axes[0].set_xlabel("")
            axes[0].set_ylabel("Number of Halting Vehicles")
        else:
            axes[0].text(0.5, 0.5, "No Summary Data", ha="center")

        # Queue Plot: Queueing Time over Timestep
        if not queue_df.empty:
            sns.lineplot(data=queue_df, x="timestep", y="queueing_time", ax=axes[1])
            axes[1].set_title("Queueing Time Over Simulation")
            axes[1].set_xlabel("")
            axes[1].set_ylabel("Queueing Time")
        else:
            axes[1].text(0.5, 0.5, "No Queue Data", ha="center")

        # Emission Plot: CO2 Emissions over Time
        if not emission_df.empty:
            sns.lineplot(data=emission_df, x="time", y="CO2", ax=axes[2])
            axes[2].set_title("CO2 Emissions Over Time")
            axes[2].set_xlabel("Time (s)")
            axes[2].set_ylabel("CO2 (g)")
        else:
            axes[2].text(0.5, 0.5, "No Emission Data", ha="center")

        plt.tight_layout()
        # Save or show based on configuration
        execution_settings = self.config.get('execution_settings', {})
        if execution_settings.get('save_results_plots', False):
            output_path = self.simulation_outputs / "results_analysis.png"
            plt.savefig(output_path, dpi=150)
            self.logger.info(f"Results analysis figure saved to {output_path}")
        if execution_settings.get('show_results_plots', False):
            plt.show()
        plt.close()

    def analyze_results(self) -> None:
        """
        Main method to perform analysis of simulation outputs and generate plots.
        """
        self.logger.info("Starting detailed simulation results analysis.")
        self.plot_analysis()
        self.logger.info("Detailed simulation results analysis completed.")

    def execute(self) -> None:
        """
        Executes the ResultsAnalyzer task.
        """
        self.analyze_results()

if __name__ == "__main__":
    # For testing purposes, initialize AppContext with the main configuration file.
    from modules.core.app_context import AppContext
    app_context = AppContext("configurations/main_config.yaml")
    analyzer = AnalysisPreparer(app_context)
    analyzer.execute()


