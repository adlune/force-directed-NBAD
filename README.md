# Fruchterman-Reingold Network Behavior Anomaly Detection Simulation

A network behavior anomaly detection system that models traffic as a graph, applies a Fruchterman-Reingold force-directed simulation, and identifies attacks by monitoring the physical observables of the simulation.

## General Information

- **Version:** 0.1.0 (initial development)
- **Date created:** 2026-09-02
- **Status:** In active development

## Project Overview

This project investigates whether force-directed graph algorithms can serve as the basis for a network behavior intrusion detection system.

#### Main Idea:
Network traffic between hosts define a graph, IP addresses are nodes and communications are edges. When this graph is laid out using a Fruchterman-Reingold model, nodes that communicate frequently are pulled together by attractive spring forces, while all nodes repel each other to prevent overlap. The system reaches an equilibrium where the layout reflects the communication structure of the network.

#### How does it differentiate benign behavior from attacks?

When an attack happens, the graph structure changes abruptly. When a port scan happens, it creates a burst of new edges from a single source to many targets. When a DDoS attack happens, it funnels edges from many sources toward one victim. These structural changes disrupt the simulation's equilibrium, producing spikes in total system energy, node displacements, and delayed convergence. By tracking these simulation observables over time and comparing them to benign behavior, the system flags anomalous time windows.

This approach is a form of novelty detection, which consists in using  a reference of normal behavior (assumed clean data) from traffic assumed to be benign, so that time windows that deviate from that (unknown data) are flagged. The method does not require labelled attack examples, but it does depend on a clean reference period. Labels are used only to evaluate the detector.

### Dataset

This project uses the CICIDS2017 dataset from the University of New Brunswick along the Canadian Institute for Cybersecurity. It has labeled network flows over five days, covering benign traffic and multiple attack types.

Source: https://www.unb.ca/cic/datasets/ids-2017.html

The project uses the flow files from `GeneratedLabelledFlows.zip`, because they are the only CSV release that keeps the Source IP, Destination IP and Timestamp columns needed to build a graph per time window.

## Model

According to Fruchterman and Reingold, two forces act on the nodes. For two nodes separated by a distance $d$, every pair repels with a force of magnitude

$$
f_r(d) = \frac{k^2}{d},
$$

and every pair of nodes joined by an edge attracts with a force of magnitude

$$
f_a(d) = \frac{d^2}{k}.
$$

Repulsion is strong when nodes are close and fade with distance, which keeps nodes from overlapping. Attraction behaves like a spring that grows stronger as connected nodes move apart, which keeps communicating hosts together. The constant $k$ is the ideal distance between nodes, computed from the area of the drawing frame.

## Project Structure

```
force-directed-NBAD/
├── data/                      # CICIDS2017 CSV files (untracked)
├── src/
│   ├── graph_builder.py       # CSV to graph construction
│   ├── force_simulation.py    # Force model and position updates
│   ├── metrics.py             # Energy, displacement, convergence extraction
│   ├── detector.py            # Anomaly flagging
│   └── visualizer.py          # Animation of the simulation
├── notebooks/
│   ├── 01_data_exploration.ipynb
│   ├── 02_baseline_simulation.ipynb
│   ├── 03_attack_simulation.ipynb
│   └── 04_detection_evaluation.ipynb
├── tests/
│   ├── test_forces.py         # Unit tests for force calculations
│   └── test_convergence.py    # Two-node equilibrium and convergence on simple graphs
├── results/                   # Output plots and metrics (untracked)
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

The CICIDS2017 dataset must be downloaded separately. Download `GeneratedLabelledFlows.zip` from the dataset page and place the CSV files from its `TrafficLabelling` folder into the `data/` directory.

## Usage

This project is in early development. Usage instructions and example workflows will be added as the implementation progresses through its development phases.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for the full text.

## Contact Information

- **Author:** Adrian Lara *[Undergraduate student in "Tecnologías para la Información en Ciencias" at Universidad Nacional Autónoma de México (UNAM)]*.
- **Contact:** adrianlarasc@gmail.com

## Acknowledgements

This project was developed as part of a Modeling and Simulation course.

Development was assisted by Claude Code Opus 5.5 (Anthropic). All code and documentation were reviewed by the author. AI assistance was used as a collaborative tool to support the learning and development process.

### Key References

The theoretical foundation for this project draws from the following works.

1. Eades, P. (1984). "A heuristic for graph drawing." *Congressus Numerantium*, 42, 149-160.
2. Fruchterman, T. and Reingold, E. (1991). "Graph drawing by force-directed placement." *Software: Practice and Experience*, 21(11), 1129-1164.
3. Barnes, J. and Hut, P. (1986). "A hierarchical O(N log N) force-calculation algorithm." *Nature*, 324, 446-449.
4. Jacomy, M., Venturini, T., Heymann, S. and Bastian, M. (2014). "ForceAtlas2, a Continuous Graph Layout Algorithm for Handy Network Visualization Designed for the Gephi Software." *PLoS ONE*, 9(6), e98679.
5. Tolle, J. and Niggemann, O. (2000). "Supporting intrusion detection by graph clustering and graph drawing." *Proc. 3rd International Workshop on Recent Advances in Intrusion Detection (RAID 2000)*, LNCS 1907.
