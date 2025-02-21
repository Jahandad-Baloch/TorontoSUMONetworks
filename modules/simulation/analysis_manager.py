# modules/simulation/simulation_analysis_manager.py

from __future__ import annotations
import os
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from modules.core.simulation_task import SimulationTask
from modules.common.command_executor import CommandExecutor
from modules.core.app_context import AppContext

class ExternalResultsAnalyzer(SimulationTask):
    """Generates analysis plots by invoking external SUMO visualization tools.
    
    This analyzer builds commands to call SUMO tools (e.g. plot_summary.py)
    and runs them via a command executor.
    """

    def __init__(self, app_context: AppContext) -> None:
        super().__init__(app_context)
        self.executor = CommandExecutor(logger=self.logger)
        # Setup simulation output directory and tool paths.
        net_area = self.config['network']['area']
        self.network_name = net_area[self.config['network']['extent']] \
                              .replace(' ', '_').lower() if self.config['network']['extent'] == 'by_junctions' \
                              else net_area.replace(' ', '_').lower()
        self.simulation_outputs = Path(self.config['paths']['simulation_data']) / self.network_name
        # Assume sumo_tools is defined in paths (with a fallback)
        # self.sumo_tools_path = Path(self.config['paths'].get('sumo_tools', os.getenv("SUMO_HOME", "") + "/tools"))

        sumo_home = os.environ.get('SUMO_HOME')
        if not sumo_home:
            raise EnvironmentError("SUMO_HOME environment variable not set.")
        self.sumo_tools_path = Path(sumo_home) / "tools"

        self.visualization_dir = self.sumo_tools_path / "visualization"
        self.xml_plotter = self.visualization_dir / "plotXMLAttributes.py"
        self.summary_plotter = self.visualization_dir / "plot_summary.py"
        # Retrieve latest output files
        self.summary_file = self._get_latest_file("summary_")
        self.queue_file = self._get_latest_file("queue_")
        self.emission_file = self._get_latest_file("emission_")

    def _get_latest_file(self, prefix: str) -> str:
        files = sorted([f for f in os.listdir(self.simulation_outputs) if f.startswith(prefix)])
        return str(self.simulation_outputs / files[-1]) if files else ""

    def get_summary_command(self) -> List[str]:
        summary_output = str(self.simulation_outputs / "summary_external.png")
        cmd = [
            "python", str(self.summary_plotter),
            "-i", self.summary_file,
            "-o", summary_output,
            "-m", "halting",
            "--xlim", "28800,34200",
            "--ylim", "0,200",
            "--xlabel", "time",
            "--ylabel", "halting_vehicles",
            "--title", "External: Halting Vehicles Over Time"
        ]
        return cmd

    def get_emission_command(self) -> List[str]:
        emission_output = str(self.simulation_outputs / "emission_external.png")
        cmd = [
            "python", str(self.xml_plotter), self.emission_file,
            "-o", emission_output,
            "--xattr", "time", "--yattr", "CO2",
            "--xlabel", "time", "--ylabel", "CO2",
            "--title", "External: CO2 Emissions Over Time"
        ]
        return cmd

    def get_queue_command(self) -> List[str]:
        queue_output = str(self.simulation_outputs / "queue_external.png")
        cmd = [
            "python", str(self.xml_plotter), self.queue_file,
            "-i", "queueing_time",
            "--filter-ids", "1138214_0",
            "-x", "timestep", "-y", "queueing_time",
            "-o", queue_output
        ]
        return cmd

    def execute(self) -> None:
        self.logger.info("Starting external results analysis.")
        commands = []
        analysis_settings = self.config.get("analysis_settings", {})
        if analysis_settings.get("analyze_summary", False):
            commands.append(self.get_summary_command())
        if analysis_settings.get("analyze_emission", False):
            commands.append(self.get_emission_command())
        if analysis_settings.get("analyze_queue", False):
            commands.append(self.get_queue_command())
        for cmd in commands:
            self.logger.info("Running external analysis command: " + " ".join(cmd))
            self.executor.run_command(cmd)
        self.logger.info("External results analysis completed.")

class InMemoryResultsAnalyzer(SimulationTask):
    """Performs in-memory analysis of simulation outputs using Pandas and Seaborn.

    It parses simulation output XML files into DataFrames and creates multi-panel plots.
    """

    def __init__(self, app_context: AppContext) -> None:
        super().__init__(app_context)
        net_area = self.config['network']['area']
        self.network_name = net_area[self.config['network']['extent']] \
                              .replace(' ', '_').lower() if self.config['network']['extent'] == 'by_junctions' \
                              else net_area.replace(' ', '_').lower()
        self.simulation_outputs = Path(self.config['paths']['simulation_data']) / self.network_name

    def _parse_xml_to_df(self, xml_path: str, element_tag: str, attributes: List[str]) -> pd.DataFrame:
        try:
            tree = ET.parse(xml_path)
            root = tree.getroot()
            records = []
            for elem in root.findall(f".//{element_tag}"):
                record = {attr: float(elem.get(attr)) if elem.get(attr) and elem.get(attr).replace('.', '', 1).isdigit() 
                          else elem.get(attr) for attr in attributes}
                records.append(record)
            if records:
                return pd.DataFrame(records)
            else:
                self.logger.warning(f"No elements found for tag {element_tag} in {xml_path}")
                return pd.DataFrame()
        except Exception as e:
            self.logger.error(f"Error parsing XML file {xml_path}: {e}")
            return pd.DataFrame()

    def _get_latest_file(self, prefix: str) -> str:
        files = sorted([f for f in os.listdir(self.simulation_outputs) if f.startswith(prefix)])
        return str(self.simulation_outputs / files[-1]) if files else ""

    def analyze_summary(self) -> pd.DataFrame:
        summary_file = self._get_latest_file("summary_output")
        df = self._parse_xml_to_df(summary_file, "interval", ["begin", "end", "halting"])
        if not df.empty:
            df["time_mid"] = (df["begin"] + df["end"]) / 2
        return df

    def plot_summary(self) -> None:
        df = self.analyze_summary()
        if df.empty:
            self.logger.warning("No summary data available for in-memory analysis.")
            return
        plt.figure(figsize=(10, 6))
        sns.lineplot(data=df, x="time_mid", y="halting")
        plt.title("In-Memory: Halting Vehicles Over Time")
        plt.xlabel("Time (s)")
        plt.ylabel("Number of Halting Vehicles")
        output_path = self.simulation_outputs / "summary_inmemory.png"
        plt.savefig(output_path, dpi=150)
        plt.close()
        self.logger.info(f"In-memory summary plot saved to {output_path}")

    def execute(self) -> None:
        self.logger.info("Starting in-memory results analysis.")
        self.plot_summary()
        self.logger.info("In-memory results analysis completed.")

class AnalysisManager(SimulationTask):
    """Facade that manages simulation output analysis using external and in-memory methods.
    
    Based on configuration, it runs external analysis (via SUMO tools) and/or in-memory
    analysis (using Pandas/Seaborn).
    """

    def __init__(self, app_context: AppContext) -> None:
        super().__init__(app_context)
        self.config = app_context.config
        self.external_analyzer = ExternalResultsAnalyzer(app_context)
        self.inmemory_analyzer = InMemoryResultsAnalyzer(app_context)

    def execute(self) -> None:
        analysis_settings = self.config.get("analysis_settings", {})
        if analysis_settings.get("external_analysis", False):
            self.logger.info("Executing external analysis...")
            self.external_analyzer.execute()
        if analysis_settings.get("inmemory_analysis", False):
            self.logger.info("Executing in-memory analysis...")
            self.inmemory_analyzer.execute()
        self.logger.info("Simulation analysis completed.")