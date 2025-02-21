# modules/simulation/interactive_map_visualizer.py

""" 
This module provides an interactive map using plotly that displays the entire traffic network and an Animated Traffic Flow using plotly for a given simulation.

Dynamic Network Map:

    - Features:
        - Displays the network layout with edges and junctions.
        - Displays traffic signal locations.
        - Displays traffic light states.
        - Displays vehicle positions.
        - Zooming, panning, and tooltips on intersections that reveal real-time simulation statistics (e.g., congestion levels, average waiting time, signal timing details).
        - Color-coded lanes or intersections based on metrics like vehicle density or emission levels.

Animated Traffic Flow:
Develop an animation of vehicle movements over time on the map.

Approach:
Use Plotly's animation capabilities to transition between time steps.
Allow users to interact with the timeline (via sliders) to view how traffic conditions evolve.

"""

# Import required libraries
import os
import plotly.graph_objects as go
import pandas as pd
import geopandas as gpd
import numpy as np
import json
from shapely.geometry import Point
from plotly.subplots import make_subplots
from plotly.offline import plot
from plotly import express as px
from plotly import io as pio
from plotly import colors

from modules.core.app_context import AppContext
from modules.common.command_executor import CommandExecutor
from modules.common.edge_types_xml import EdgeTypesXML
from modules.network.centreline_processor import CentrelineProcessor
from modules.common.geo_utils import GeoUtils


# InteractiveMapVisualizer class
class Interactive
