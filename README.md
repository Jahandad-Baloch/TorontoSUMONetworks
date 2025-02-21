TorontoSUMONetworks
TorontoSUMONetworks is an open-source simulation framework built on top of the Simulation of Urban MObility (SUMO) tool. It enables researchers, urban planners, and transportation engineers to create, manipulate, simulate, and analyze realistic traffic networks with real-world data. Whether you are exploring adaptive traffic signal control (ATSC) via multiagent reinforcement learning (MARL) or investigating comprehensive urban traffic management strategies, TorontoSUMONetworks provides a robust, modular platform for your research and planning needs.

## Table of Contents
1.  [Introduction](#introduction)
2.  [Features](#features)
3.  [Project Architecture and Modules](#project-architecture-and-modules)
4.  [Installation and Setup](#installation-and-setup)
5.  [Configuration](#configuration)
6.  [Usage](#usage)
7.  [Troubleshooting](#troubleshooting)
8.  [Upcoming Features](#upcoming-features)
9.  [Contributing](#contributing)
10. [License](#license)
11. [Contact](#contact)

## Introduction
Urban mobility and efficient traffic management are essential in modern cities. TorontoSUMONetworks provides a flexible, end-to-end platform to simulate and analyze urban traffic networks using SUMO. The project supports various research areas, including:

*   Intelligent Transportation Systems (ITS)
*   Multiagent Reinforcement Learning (MARL) for Adaptive Traffic Signal Control (ATSC)
*   Multi-modal transportation analysis

By integrating real-world data—from city boundaries and centreline geojsons to traffic volumes and GTFS schedules—the framework delivers realistic simulations that help optimize urban traffic flow, reduce congestion, and improve public transport performance.

## Features
*   **Realistic Traffic Simulation**: Build and simulate detailed networks encompassing major arterials, local streets, intersections, and public transit routes.
*   **Multi-Modal Transport Support**: Simulate various transportation modes such as private vehicles, buses, trucks, bicycles, and pedestrians.
*   **Extensive Configurability**: Tailor every aspect of the simulation via YAML configuration files—network extent, traffic parameters, detector setups, routing, and analysis options.
*   **Advanced Data Integration**: Process real-world datasets (e.g., City of Toronto Open Data) alongside centreline and boundary data to generate accurate networks.
*   **Adaptive Traffic Signal Control (ATSC)**: Experiment with MARL-based ATSC strategies using configurable traffic detectors and dynamic simulation outputs.
*   **Modular and Extensible**: With clearly separated modules for network building, traffic data integration, route management, and simulation analysis, the project can be easily extended for additional research scenarios.

## Project Architecture and Modules
The project is organized into several key directories:

*   **configurations/**:
    Contains YAML files to control simulation parameters, network settings, traffic data processing, routing, and analysis. Key files include:
    *   `main_config.yaml`
    *   `network_config.yaml`
    *   `traffic_config.yaml`
    *   `simulation_config.yaml`
    *   `detectors_config.yaml`
    *   `paths_config.yaml`
    *   `routing_config.yaml`
    *   `analysis_config.yaml`
    *   (and others as needed)
*   **data/**:
    Structured into:
    *   `raw/`: Original datasets (e.g., geojsons, CSVs, GTFS).
    *   `processed/`: Data processed for simulation inputs.
    *   `simulation_output/`: Output from SUMO simulations including emission and summary reports.
    *   `sumo_networks/`: Generated SUMO network files and related XML configurations.
*   **modules/**:
    Houses the source code, divided into:
    *   `common/`: Shared utilities such as command execution, XML generation, and plotting.
    *   `core/`: Fundamental classes and simulation task definitions.
    *   `download/`: Modules to download and update datasets.
    *   `network/`: Tools for processing centreline data, building the network, and handling boundaries.
    *   `route/`: Modules for managing vehicle routes and random trip generation.
    *   `simulation/`: Scripts for running simulations and analyzing outputs.
    *   `traffic/`: Integration and processing of traffic data, detector configuration, and turning movements.
*   **docs/**: Additional documentation.
*   **logs/**: Log files for tracking simulation processes.
*   `main.py`: The primary script that orchestrates the simulation workflow.
*   `requirements.txt`: Lists Python dependencies.
*   `.gitignore`, `LICENSE`, etc.

## Installation and Setup

### Prerequisites
*   Python: Version 3.8 or newer.
*   SUMO: Version 1.9.0 or later.

### Step-by-Step Installation
1.  **Clone the Repository**
    ```bash
    git clone https://github.com/your-username/TorontoSUMONetworks.git
    cd TorontoSUMONetworks
    ```
2.  **Set Up a Virtual Environment (Recommended)**
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate  # On Windows: .venv\Scripts\activate
    # If on Windows, connecting to WSL is recommended
    ```
3.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```
4.  **Configure SUMO Environment Variables**

    Ensure that SUMO is installed and set the environment variables:
    ```bash
    export SUMO_HOME="/path/to/sumo"  # Example: export SUMO_HOME="/usr/share/sumo"
    export PATH="$PATH:$SUMO_HOME/bin"
    ```
5.  **Verify Installation**

    Run `sumo --version` to check that SUMO is correctly installed.

## Configuration
Before running a simulation, review the YAML configuration files in the `configurations/` folder. Key files include:

*   `main_config.yaml`: Controls the overall simulation process (data fetching, network building, simulation execution, etc.).
*   `network_config.yaml`: Defines the simulation area, extent (e.g., `city_wide`, `by_ward_name`, or `by_junctions`), and network type.
*   `traffic_config.yaml`: Sets parameters for traffic demand and data processing.
*   `simulation_config.yaml`: Specifies simulation time frames, output options, and performance metrics.
*   `detectors_config.yaml`: Configures the placement of traffic detectors (E1, E2, etc.).
*   `routing_config.yaml`: Adjusts vehicle routing options and random trip generation settings.
*   `analysis_config.yaml`: Details the analysis metrics for simulation outputs.

Make sure that directory paths (set in `paths_config.yaml`) correctly point to your raw data, processed data, and output folders.

## Usage
### Running a Simulation
The primary entry point is `main.py`, which orchestrates the entire simulation workflow:

```bash
python main.py --config configurations/main_config.yaml
```

### Execution Flow Overview
1. **Data Fetching**: (Optional) Downloads raw datasets if enabled.
2. **Network Building**: Processes centreline data and boundaries (using modules in `modules/network/`) to create a SUMO network.
3. **Detector Placement**: Configures and integrates traffic detectors based on your settings.
4. **Traffic Data Processing**: Processes traffic volume data to generate turning movements and edge weight files.
5. **Route Generation**: Creates vehicle routes, including options for random trip generation and GTFS-based public transport routes.
6. **Simulation Execution**: Runs the SUMO simulation using a composed configuration file.
7. **Analysis**: Processes simulation outputs to compute key metrics such as queue lengths and emissions.

### Example Configuration Excerpt
An excerpt from `configurations/main_config.yaml`:

```yaml
execution_settings:
  fetch_data: false
  build_network: true
  network_extent: "by_ward_name"
  build_detectors: true
  process_traffic_data: true
  generate_routes: true
  compose_sumocfg: true
  run_simulation: true
  analyze_results: true
```

### Module Highlights
- **TrafficNetworkCreation** (in `modules/network/`): Builds the SUMO network by processing centreline geojson data, applying area filters, and extracting junction and traffic signal information.
- **CentrelineProcessor** (in `modules/network/`): Filters and processes centreline data based on active types and area boundaries.
- **TrafficDataIntegrator** (in `modules/traffic/`): Integrates processed traffic volume data with the SUMO network, generating XML files for turning movements and edge weights.
- **SumoRouteManager** (in `modules/route/`): Manages the generation of random trips and vehicle routes, including GTFS import for public transport routes.

## Troubleshooting
If you encounter issues during installation or simulation, consider the following steps:

1. **SUMO Environment**: Double-check that the `SUMO_HOME` variable is set correctly and that the SUMO binaries are in your `PATH`.
2. **Configuration Files**: Ensure that all YAML configuration files are properly formatted and that file paths are accurate.
3. **Dependencies**: Reinstall or update dependencies by running `pip install -r requirements.txt` again.
4. **Logs**: Inspect the `logs/` directory for detailed error messages.
5. **Data Availability**: Confirm that raw datasets are present in `data/raw/` and accessible to the scripts.
6. **Module-Specific Errors**: Check the logging output from modules such as `TrafficDataProcessor` or `CentrelineProcessor` for hints on missing data or misconfigurations.

## Upcoming Features
- Real-time incident management and lane closure simulation
- Integration of emergency vehicle routing
- Enhanced X2X communication scenario modeling
- Additional routing algorithms and traffic signal programs
- Improved visualization tools for simulation outputs

## Contributing
Contributions are welcome! If you have suggestions, bug reports, or feature enhancements, please open an issue or submit a pull request. For guidelines on contributing, refer to the `CONTRIBUTING.md` file.

## License
This project is licensed under the MIT License.

## Contact
For questions, suggestions, or support, please contact the project maintainer:

**Jahandad Baloch**
- GitHub: [@Jahandad-Baloch](https://github.com/Jahandad-Baloch)