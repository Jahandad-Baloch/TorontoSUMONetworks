# TorontoSUMONetworks

TorontoSUMONetworks is an open-source project designed to provide a comprehensive platform for the creation, manipulation, and simulation of traffic networks using the Simulation of Urban MObility (SUMO) tool. This repository is particularly valuable for research in transportation systems, urban planning, and traffic management. It is flexible enough to support a variety of research areas, including Intelligent Transportation Systems (ITS), Multiagent Reinforcement Learning (MARL) for Adaptive Traffic Signal Control (ATSC), and more.

## Table of Contents
- [Introduction](#introduction)
- [Features](#features)
- [Installation](#installation)
- [Project Structure](#project-structure)
- [Usage](#usage)
- [Configurations](#configurations)
- [Upcoming Features](#upcoming-features)
- [Contributing](#contributing)
- [License](#license)
- [Contact](#contact)

## Introduction

Urban mobility and efficient traffic management are critical components of modern cities. TorontoSUMONetworks provides a realistic simulation environment for modeling and analyzing transportation systems. This platform is designed to be versatile, supporting a wide range of applications such as traffic management, urban planning, and ITS research.

Whether you are a transportation engineer, urban planner, or researcher, this tool allows you to create, simulate, and analyze traffic scenarios to improve urban infrastructure, reduce congestion, and enhance overall mobility. The project is also well-suited for specialized research in MARL for ATSC, providing the tools needed to simulate multi-agent interactions within complex traffic networks.

## Features

- **Realistic Traffic Simulation**: Build and simulate the traffic network of Toronto, including major arterials, local streets, intersections, and public transportation routes.
- **Multi-Modal Transportation**: Support for simulating various transportation modes, including private vehicles, buses, bicycles, and pedestrians.
- **Flexible Use Cases**: Applicable to various fields, including transportation systems, urban planning, and ITS research.
- **Adaptive Traffic Signal Control**: Test and develop MARL-based ATSC systems to optimize traffic flow and reduce congestion.
- **Configurable Detectors**: Easily configure and place E1 induction loops, E2 lane area detectors, and E3 multi-entry/multi-exit detectors at traffic intersections.
- **Data-Driven Simulation**: Utilize real-world datasets from the City of Toronto Open Data Portal for accurate traffic volume, signal timing, and route planning.
- **Extensive Configuration Options**: Customize every aspect of the simulation, from network building to traffic demand generation and simulation parameters.

## Installation

### Prerequisites

Ensure that you have the following software installed:

- Python 3.8+
- SUMO 1.9.0 or newer

### Step-by-Step Installation Guide

1. **Clone the Repository**:
    ```bash
    git clone https://github.com/Jahandad-Baloch/TorontoSUMONetworks.git
    cd TorontoSUMONetworks
    ```

2. **Setup Virtual Environment** (optional but recommended):
    ```bash
    python3 -m venv venv
    source venv/bin/activate # or venv\Scripts\activate on Windows
    ```

3. **Install Required Packages**:
    ```bash
    pip install -r requirements.txt
    ```

4. **Set Up SUMO Environment Variables**:
    ```bash
    export SUMO_HOME="/usr/share/sumo"
    export PATH="$PATH:$SUMO_HOME/bin"
    ```

5. **Run the Main Script**:
    ```bash
    python main.py --config configurations/main_config.yaml
    ```

## Project Structure

```plaintext
TorontoSUMONetworks/
├── configurations/                   # Configuration files for traffic networks and simulations
├── data/                             # Data files for traffic simulation
│   ├── raw/                          # Toronto transportation datasets
│   ├── processed/                    # Processed data for SUMO simulation
│   ├── sumo_networks/                # SUMO network files
│   ├── simulation_output/            # Output files from SUMO simulation
├── logs/                             # Log files for data processing and simulation
├── scripts/                          # Python scripts for data processing and simulation
│   ├── build_sumo_net/               # Scripts for building SUMO networks
│   ├── common/                       # Common utility scripts
│   ├── fetch_data/                   # Scripts for fetching Toronto transportation data
│   ├── results_analysis/             # Scripts for analyzing simulation results
│   ├── simulation/                   # Scripts for managing SUMO simulations
│   ├── sumo_tools/                   # Scripts for SUMO-specific tools like detector generation
│   ├── traffic_data_processing/      # Scripts for processing traffic data
├── LICENSE                           # License file
├── main.py                           # Main script for running the project
├── README.md                         # Project README file
├── requirements.txt                  # Python package requirements
```

## Usage

### Running Simulations

#### Configure Your Simulation:
- Modify the configuration files in the `configurations/` directory to specify network parameters, traffic data, and simulation settings.

#### Run the Simulation:
- Execute the following command to run the simulation:

    ```bash
    python main.py --config configurations/main_config.yaml
    ```

#### Processed Traffic Data and Simulation Output:
- The simulation results to be stored can be enabled/disabled using configurations and are stored in `data/simulation_output/{Network Name}` Depending on the use case, users can perform various analysis on the types of outputs saved. 
- The outputs can be further extended by making changes in method `SimulationManager._extend_output_options() inside scripts/simulation/simulation_manager.py` For the common analysis operations using the SUMO provided tools, see the `scripts/results_analysis/`

## Configurations

TorontoSUMONetworks provides a variety of configuration files to customize the simulation environment:

- **`main_config.yaml`**: Central configuration file to control the overall simulation process, including network extent, detector placement, and traffic demand.
- **`network_config.yaml`**: Configure the area and type of the network to build, such as city-wide or by specific wards/neighborhoods.
- **`traffic_config.yaml`**: Set up the parameters for traffic demand generation, including vehicle types and public transit.
- **`simulation_config.yaml`**: Define the simulation parameters, such as duration, time step, and output files.
- **`detectors_config.yaml`**: Configure E1, E2, and E3 detectors for monitoring traffic flow and signal performance.
- **`paths_config.yaml`**: Set up paths for project directories and files.
- **`routing_config.yaml`**: Customize the routing algorithms and vehicle routes used in the simulation.
- **`analysis_config.yaml`**: Define the parameters for analyzing simulation results, including queue lengths, emissions, and vehicle routes.


## Example Usage

`main.py` is the primary script that runs the simulation. It takes a configuration file as an argument, with the default being `configurations/main_config.yaml`. The main configuration file imports and loads other configurations necessary for the simulation process.

### Example Scenario

**`configurations/main_config.yaml`:**

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

**`configurations/network_config.yaml`:**

```yaml
network_settings:
  by_ward_name:
      network_area: "Scarborough North"
      network_type: "arterial"
```

**`configurations/lanes_config.yaml`:**

```yaml
arterial_lanes:
  - "Expressway"
  - "Major Arterial"
  - "Minor Arterial"
  - "Expressway Ramp"
  - "Major Arterial Ramp"
  - "Minor Arterial Ramp"
  - "Busway"
  - "Collector"
  - "Collector Ramp"
  - "Access Road"
```

**`configurations/simulation_config.yaml`:**

```yaml
simulation_settings:
  simulate_public_transport: true
  begin: 28800
  end: 34200
  add_induction_loops: true
  save_output: true
  summary_output: true
  emission_output: true
```

**`configurations/analysis_config.yaml`:**

```yaml
analysis_settings:
  analyze_summary: true
```
### Execute `main.py`

With the above configuration settings, running the `main.py` script will trigger the following sequence of events:

1. **Data Fetching**: The script will would fetch the required datasets from the City of Toronto's Open Data Portal set to `True` in `configurations/datasets_config.yaml`. If the datasets are already available, it will skip downloading them.

2. **Network Building**: The script will build the SUMO network for the "Scarborough North" ward area, including only the major arterial lanes, as specified by `network_extent: "by_ward_name"` and `network_area: "Scarborough North"`. The lane types are defined in `configurations/lanes_config.yaml`. The network will be saved as `data/sumo_networks/scarborough_north/scarborough_north_arterial.net.xml`. This file can be viewed in the SUMO netedit tool and SUMO GUI. 
    ```bash
    netedit data/sumo_networks/scarborough_north/scarborough_north_arterial.net.xml
    ```

3. **Detector Placement**: Detectors like induction loops will be placed at the traffic light junctions using the settings provided in the `detectors_config.yaml`. The detector files will be saved in `data/sumo_networks/scarborough_north/`.

4. **Traffic Data Processing**: The script will process the traffic volume data from the City of Toronto's `data/raw/traffic-volumes-at-intersections-for-all-modes/raw-data-2020-2029.csv` dataset and create the necessary files, such as turn counts (`turning_movements.xml`) and store processed data in `data/processed/scarborough_north/`.

5. **Route Generation**: Using the processed traffic data, the script will use turn counts generate vehicle routes (`scarborough_north_routes.rou.xml`), including bus routes (`scarborough_north_public_transport.rou.xml`) and an additional bus stops file (`scarborough_north_gtfs_routes.add.xml`) derived from the GTFS dataset (`TTC_Routes_and_Schedules_Data.zip`).

6. **SUMO Configuration File**: The `compose_sumocfg` step will create a SUMO configuration file (`scarborough_north_sumo_cfg.sumocfg`) with input elements such as the input net-files, route-files, additional-files, time settings and other elements required to run the simulation. This file is composed based on the settings in `simulation_config.yaml`.

7. **Simulation Execution**: The SUMO simulation will run based on the composed configuration, adhering to the time settings (8:00 AM to 9:30 AM) and will generate output data such as queue lengths, emissions, and summary statistics based on the settings in `simulation_config.yaml`.

8. **Analysis**: Once the simulation is complete, the script will generate and store the simulation results in `data/simulation_output/scarborough_north/`. For example, it will store `summary_output{timestamp}` and analyze the results based on the parameters set in `analysis_config.yaml`.

9. **Outputs**: The results and data generated by the simulation and analysis phases will be saved according to the output settings in `simulation_config.yaml`.


## Upcoming Features

- Support for real-time incident management and lane closures.
- Integration of emergency vehicle routing.
- Development of X2X communication scenarios.
- Implementation of additional routing algorithms and traffic signal programs used by the City of Toronto.
- Enhanced visualization tools for simulation results.

## Contributing

We welcome contributions from the community to enhance TorontoSUMONetworks! To contribute:

1. Fork the repository.
2. Create a new branch (`git checkout -b feature/AwesomeFeature`).
3. Commit your changes (`git commit -am 'Add AwesomeFeature'`).
4. Push to the branch (`git push origin feature/AwesomeFeature`).
5. Create a Pull Request.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more details.

## Contact

For questions, suggestions, or support, please contact the project maintainer:

**Jahandad Baloch**  
[Email](mailto:jahandadbaloch@gmail.com)  
GitHub: [@Jahandad-Baloch](https://github.com/Jahandad-Baloch)

---

