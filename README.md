# Force-Directed N-Body Network Behavior Anomaly Detection

A network behavior anomaly detection system that models traffic flows as a graph, applies a Fruchterman-Reingold force-directed layout simulation, and identifies attacks by monitoring the physical observables of the simulation (energy, node displacement, convergence behavior).

## General Information

- **Version:** 0.1.0 (initial development)
- **Date created:** 2026-09-02
- **Status:** In active development

## Project Overview

This project investigates whether force-directed graph algorithms can serve as the basis for a network behavior intrusion detection system.

Network traffic between hosts defines a graph, IP addresses are nodes and communication flows are edges. When this graph is laid out using a Fruchterman-Reingold force model, nodes that communicate frequently are pulled together by attractive spring forces, while all nodes repel each other to prevent overlap. The system reaches an equilibrium where the layout reflects the communication structure of the network.

When an attack happens, the graph structure changes abruptly. When a port scan happens, it creates a burst of new edges from a single source to many targets. When a DDoS attack happens, it funnels edges from many sources toward one victim. These structural changes disrupt the simulation's equilibrium, producing spikes in total system energy, node displacements, and delayed convergence. By tracking these simulation observables over time and comparing them to benign behavior, the system flags anomalous time windows that likely correspond to attack activity.

### Dataset

This project uses the CICIDS2017 dataset from the University of New Brunswick along the Canadian Institute for Cybersecurity. It contains labeled network flows captured over five days in a controlled lab, covering benign traffic and multiple attack types including brute force, DoS, DDoS, botnet, port scanning, web attacks, and infiltration.

Source: https://www.unb.ca/cic/datasets/ids-2017.html

## Project Organization

```
force-directed-NBAD/
├── data/                      # CICIDS2017 CSV files (not tracked by git)
├── src/
│   ├── graph_builder.py       # CSV to graph construction (nodes, edges, weights)
│   ├── force_simulation.py    # Fruchterman-Reingold force model and position updates
│   ├── metrics.py             # Energy, displacement, convergence extraction
│   ├── detector.py            # Threshold-based anomaly flagging
│   └── visualizer.py          # Matplotlib animation of the simulation
├── notebooks/
│   ├── 01_data_exploration.ipynb
│   ├── 02_baseline_simulation.ipynb
│   ├── 03_attack_simulation.ipynb
│   └── 04_detection_evaluation.ipynb
├── tests/
│   ├── test_forces.py         # Unit tests for force calculations
│   └── test_convergence.py    # Convergence tests on known simple graphs
├── results/                   # Output plots and metrics (not tracked by git)
├── requirements.txt
├── LICENSE
└── README.md
```

## Installation

Clone the repository and set up a Python virtual environment:

```bash
git clone https://github.com/adlune/force-directed-NBAD.git
cd force-directed-NBAD
python -m venv .NBAD
source .NBAD/bin/activate # Windows: source .NBAD/Scripts/Activate
pip install -r requirements.txt
```

The CICIDS2017 dataset must be downloaded separately. Place the CSV files from `MachineLearningCSV.zip` into the `data/` directory.

## Usage

This project is in early development. Usage instructions and example workflows will be added as the implementation progresses through its development phases.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for the full text.

## Contact Information

- **Author:** Adrian Lara *[Undergraduate student in "Tecnologías para la Información en Ciencias" at Universidad Nacional Autónoma de México (UNAM)]*.
- **Contact:** adrianlara.jpg@gmail.com

## Acknowledgements

This project was developed as part of a Modeling and Simulation course.

Development was assisted by Claude Code Model Opus 4.6 (Anthropic). All code and documentation were reviewed by the author. AI assistance was used as a collaborative tool to support the learning and development process.

### Key References

The theoretical foundation for this project draws from the following works.

1. Eades, P. (1984). "A heuristic for graph drawing." *Congressus Numerantium*, 42, 149-160.
2. Fruchterman, T. and Reingold, E. (1991). "Graph drawing by force-directed placement." *Software: Practice and Experience*, 21(11), 1129-1164.
3. Barnes, J. and Hut, P. (1986). "A hierarchical O(N log N) force-calculation algorithm." *Nature*, 324, 446-449.
4. Jacomy, M., Venturini, T., Heymann, S. and Bastian, M. (2014). "ForceAtlas2, a Continuous Graph Layout Algorithm for Handy Network Visualization Designed for the Gephi Software." *PLoS ONE*, 9(6), e98679.
5. Tolle, J. and Niggemann, O. (2000). "Supporting intrusion detection by graph clustering and graph drawing." *Proc. 3rd International Workshop on Recent Advances in Intrusion Detection (RAID 2000)*, LNCS 1907.
6. Sharafaldin, I., Habibi Lashkari, A. and Ghorbani, A. A. (2018). "Toward Generating a New Intrusion Detection Dataset and Intrusion Traffic Characterization." *4th International Conference on Information Systems Security and Privacy (ICISSP)*.
