# __init__.py (inside root of our project)
"""
TorontoSUMONetworks Package

This package provides modules for downloading, processing, building, and simulating SUMO networks.
"""

# Import public symbols from the various subpackages.
from .modules.common import __all__ as common_all
from .modules.core import __all__ as core_all
from .modules.download import __all__ as download_all
from .modules.network import __all__ as network_all
from .modules.route import __all__ as route_all
from .modules.simulation import __all__ as simulation_all
from .modules.traffic import __all__ as traffic_all

# Combine the __all__ lists into one master __all__.
__all__ = (
    common_all + core_all + download_all + network_all + route_all + simulation_all + traffic_all
)