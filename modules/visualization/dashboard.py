#!/usr/bin/env python3
import os
import json
import pandas as pd
import geopandas as gpd
import plotly.express as px
import plotly.graph_objects as go
import dash
from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
import xml.etree.ElementTree as ET
from xml.dom import minidom
from modules.core.simulation_task import SimulationTask

class DashboardApp(SimulationTask):
    """
    A Dash application for visualizing traffic network data and simulation results.
    """
    def __init__(self, app_context):
        """
        Initialize the DashboardApp with the provided application context.
        
        Args:
            app_context (:obj:`AppContext`): The application context containing configuration and logger.
        """

        # Initialize AppContext and configurations
        super().__init__(app_context)
        self.app_context = app_context
        self.config = self.app_context.config
        self.paths = self.app_context.paths

        # Set up network configuration
        self._setup_network_config()
        
        # Initialize data
        self.network_geojson = self._load_network_geojson()
        self.summary_df = self._load_simulation_summary()

        # Initialize Dash app
        self.app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
        self.app.title = "TorontoSUMONetworks Dashboard"
        
        # Set up the layout
        self._create_layout()
        
        # Register callbacks
        self._register_callbacks()

    def _setup_network_config(self):
        """Set up network configuration and paths."""
        network_config = self.config['network']
        extent = network_config['extent']
        if extent == "by_junctions":
            network_area = network_config['area']['by_junctions']['name']
        else:
            network_area = network_config['area'][extent]
        self.network_name = network_area.replace(' ', '_').lower()
        self.simulation_outputs_dir = self.paths['simulation_data'] / self.network_name

    def _load_geojson(self, file_path):
        """Load GeoJSON data from the provided file path."""
        if os.path.exists(file_path):
            try:
                gdf = gpd.read_file(file_path)
                return json.loads(gdf.to_json())
            except Exception as e:
                print(f"Error loading geojson {file_path}: {e}")
                return None
        print(f"GeoJSON file not found: {file_path}")
        return None

    def _find_centreline_geojson(self):
        """Locate a GeoJSON file in the 'toronto-centreline-tcl' raw data directory."""
        centreline_dir = self.paths['raw_data'] / "toronto-centreline-tcl"
        if centreline_dir.exists():
            for file in os.listdir(centreline_dir):
                if file.endswith("4326.geojson"):
                    return os.path.join(centreline_dir, file)
        return None

    def _load_network_geojson(self):
        """Load the network GeoJSON data."""
        centreline_path = self._find_centreline_geojson()
        return self._load_geojson(centreline_path) if centreline_path else None

    # def _load_simulation_summary(self):
    #     """Load the simulation summary xml data."""
    #     summary_xml = "data/simulation_output/scarborough-guildwood/summary_output_02-14_03-46.xml"
    #     if os.path.exists(summary_xml):
    #         tree = ET.parse(summary_xml)
    #         root = tree.getroot()
    #         data = []
    #         for interval in root.findall("interval"):
    #             data.append({
    #                 "time_mid": int(interval.get("begin")) + (int(interval.get("end")) - int(interval.get("begin"))) / 2,
    #                 "halting": int(interval.get("halting"))
    #             })
    #         return pd.DataFrame(data)

    def _load_simulation_summary(self):
        """Load the simulation summary XML data."""
        summary_xml = "data/simulation_output/scarborough-guildwood/summary_output_02-14_03-46.xml"
        data = []
        if os.path.exists(summary_xml):
            try:
                tree = ET.parse(summary_xml)
                root = tree.getroot()
                for step in root.findall("step"):
                    time_str = step.get("time")
                    halting_str = step.get("halting")
                    if time_str is not None and halting_str is not None:
                        # Use the 'time' attribute as the x-axis value.
                        time_val = float(time_str)
                        halting_val = int(halting_str)
                        data.append({
                            "time_mid": time_val,
                            "halting": halting_val
                        })
            except Exception as e:
                print(f"Error parsing summary XML: {e}")
        if not data:
            # Fallback: create dummy data using simulation settings.
            start = self.config.get("simulation_settings", {}).get("begin", 28800)
            end = self.config.get("simulation_settings", {}).get("end", 34200)
            num_intervals = self.config.get("traffic_settings", {}).get("num_intervals", 6)
            interval = (end - start) // num_intervals
            time_mid = list(range(start, end + 1, interval))
            data = [{"time_mid": t, "halting": 50 + i * 10} for i, t in enumerate(time_mid)]
        return pd.DataFrame(data)


    def _create_layout(self):
        """Create the app layout with tabs."""
        map_layout = self._create_map_tab()
        analysis_layout = self._create_analysis_tab()
        configuration_layout = self._create_configuration_tab()
        
        self.app.layout = dbc.Container([
            dbc.Tabs([
                dbc.Tab(map_layout, label="Network Map"),
                dbc.Tab(analysis_layout, label="Data Analysis"),
                dbc.Tab(configuration_layout, label="Configuration")
            ])
        ], fluid=True)

    def _create_map_tab(self):
        """Create the map tab layout."""
        return dbc.Container([
            dbc.Row(dbc.Col(html.H3("Interactive Traffic Network Map"), width=12)),
            dbc.Row(dbc.Col(dcc.Graph(id="network-map"), width=12)),
            dbc.Row(dbc.Col(html.Div("Explore the network, view intersections, and see live simulation metrics."), width=12))
        ], fluid=True)

    def _create_analysis_tab(self):
        """Create the analysis tab layout."""
        return dbc.Container([
            dbc.Row(dbc.Col(html.H3("Simulation Data Analysis"), width=12)),
            dbc.Row(dbc.Col(dcc.Graph(id="analysis-chart"), width=12)),
            dbc.Row(dbc.Col(html.Div("Interactive chart showing trends (e.g., halting vehicles over time)."), width=12))
        ], fluid=True)

    # Breaking Dropped FormGroup. It is no longer necessary to use FormGroup to align components in a form. Use Row Col and gutter modifier classes and spacing utilities instead.
    def _create_configuration_tab(self):
        """Create the configuration tab layout."""
        return dbc.Container([
            dbc.Row(dbc.Col(html.H3("Simulation Configuration"), width=12)),
            dbc.Row([
                dbc.Col([
                    html.Label("Simulation Start Time (s)"),
                    dbc.Input(id="start-time", type="number",
                             value=self.config.get("simulation_settings", {}).get("begin", 28800))
                ], md=4),
                dbc.Col([
                    html.Label("Simulation End Time (s)"),
                    dbc.Input(id="end-time", type="number",
                             value=self.config.get("simulation_settings", {}).get("end", 34200))
                ], md=4),
                dbc.Col([
                    html.Label("Active Modes (comma-separated)"),
                    dbc.Input(id="active-modes", type="text",
                             value=",".join(self.config.get("traffic_settings", {}).get("active_modes", ["cars", "truck"])))
                ], md=4)
            ]),
            dbc.Row(dbc.Col(dbc.Button("Update Configuration", id="update-config", color="primary"), width="auto")),
            dbc.Row(dbc.Col(html.Div(id="config-output"), width=12))
        ], fluid=True)

    def _register_callbacks(self):
        """Register all callbacks for the app."""
        self.app.callback(
            Output("network-map", "figure"),
            Input("network-map", "id")
        )(self.update_map)

        self.app.callback(
            Output("analysis-chart", "figure"),
            Input("analysis-chart", "id")
        )(self.update_analysis_chart)

        self.app.callback(
            Output("config-output", "children"),
            Input("update-config", "n_clicks"),
            State("start-time", "value"),
            State("end-time", "value"),
            State("active-modes", "value")
        )(self.update_configuration)

    def update_map(self, dummy_input):
        """Update the interactive network map."""
        if self.network_geojson:
            fig = px.choropleth_mapbox(
                pd.DataFrame(),
                geojson=self.network_geojson,
                locations=[],
                color_discrete_sequence=["#FFFFFF"],
                center={"lat": 43.7, "lon": -79.4},
                mapbox_style="carto-positron",
                zoom=10
            )
            fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
        else:
            fig = go.Figure()
            fig.update_layout(title="Network GeoJSON not available")
        return fig

    def update_analysis_chart(self, dummy_input):
        """Update the analysis chart."""
        fig = px.line(
            self.summary_df, x="time_mid", y="halting",
            title="Halting Vehicles Over Time",
            labels={"time_mid": "Time (s)", "halting": "Number of Halting Vehicles"}
        )
        fig.update_layout(margin={"r": 20, "t": 40, "l": 20, "b": 20})
        return fig

    def update_configuration(self, n_clicks, start_time, end_time, active_modes):
        """Handle configuration updates."""
        if n_clicks:
            new_config = {
                "simulation_settings": {"begin": start_time, "end": end_time},
                "traffic_settings": {"active_modes": [mode.strip() for mode in active_modes.split(",")]}
            }
            return html.Div([
                html.H5("Configuration Updated:"),
                html.Pre(json.dumps(new_config, indent=2))
            ])
        return ""

    def execute(self, debug=True, host="0.0.0.0", port=8050):
        """Run the dashboard server."""
        self.app.run_server(debug=debug, host=host, port=port)

if __name__ == "__main__":
    dashboard = DashboardApp()
    dashboard.execute()
