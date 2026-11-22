# Efficient Traffic Rule Monitoring for Rule-Compliant Motion Planning of Automated Vehicles – Evaluation Scripts

This repository contains the evaluation scripts for the paper "Efficient Traffic Rule Monitoring for Rule-Compliant Motion Planning of Automated Vehicles" by Sebastian Maierhofer and Matthias Althoff.

<p align="center">
  <img src="assets/img_readme.jpg" alt="Rule-compliant right turn at a yield sign in CARLA" width="900"/>
  <br/>
  <em>Our planner turns right at a T-intersection with a yield sign in the CARLA simulator.
  Trajectories violating a traffic rule are shown in red, rule-compliant trajectories in green.</em>
</p>

## :link: Related Repositories

The scripts in this repository only set up and evaluate the experiments.
The monitor and the planner are implemented in the following repositories:

| Repository | Python package | Description |
|---|---|---|
| [RV-Monitors](https://github.com/CommonRoad/rv-monitors) | `rv-monitors` (`import rvm`) | C++17 runtime verification algorithms for LTLf, PLTLf, and MTL on finite traces, including our multi-head monitor with connected evaluation, short-circuiting, predicate reordering, iterative evaluation, and early termination. |
| [CommonRoad Environment Model](https://github.com/CommonRoad/environment-model) | `commonroad_cpp` (`import crcpp`) | C++17 representation of CommonRoad scenarios and implementation of the predicates and functions of the formalized traffic rules. |
| [CommonRoad Traffic Rule Monitor](https://github.com/CommonRoad/commonroad-monitor) | `commonroad_monitor` (`import crmonitor`) | Traffic rule specifications and monitor that combines RV-Monitors and the environment model; provides the C++ and Python interfaces. |
| [CommonRoad Reactive Planner](https://github.com/CommonRoad/commonroad-reactive-planner) | `commonroad-reactive-planner` | Sampling-based motion planner into which the monitor is integrated. |
| [CommonRoad Prediction](https://github.com/CommonRoad/commonroad-prediction) | `commonroad-prediction` | Constant-velocity prediction of other traffic participants. |
| [CommonRoad-CARLA Interface](https://github.com/CommonRoad/commonroad-carla-interface) | `commonroad-carla-interface` | Interface to the CARLA simulator (only required for the interactive simulations). |

All of them are pre-installed in the Docker image described [below](#computer-getting-started) at the versions used for the paper.

## :file_folder: Overview

```tree
.
├── assets/                     # Image for this README
├── configurations/
│   ├── motivating_examples/    # Planner configuration for the motivating example
│   ├── planning/               # Planner configurations for each planning scenario
│   ├── predicates/             # Predicate costs and satisfaction probabilities (used for reordering)
│   ├── rv_monitor/             # Parameters of the evaluation on artificial specifications and traces
│   └── set_based/              # Planner configurations for the set-based evaluation
├── scenarios/                  # CommonRoad scenarios
│   ├── motivating_examples/
│   ├── planning/
│   └── set_based/
├── src/evaluation/             # Source code of the experiments
│   └── monitor/exec/           # Formula and trace generators gen_fmla and gen_log (see below)
├── tools/                      # Helper scripts and evaluations that are not part of the paper
└── *.py                        # Main scripts for the evaluation: see below for details
```

## :computer: Getting Started

1. Pull the Docker image from the GitHub container registry (Docker may require `sudo` if your user is not in the `docker` group):
```bash
docker pull ghcr.io/commonroad/traffic-rule-monitoring/traffic-rule-monitoring:latest
```
Alternatively, you can build the image yourself.
The image is built from local checkouts of the CommonRoad tools, which `docker/prepare_sources.sh` copies into `docker/sources/` (by default from the parent directory of this repository):
```bash
docker/prepare_sources.sh
docker build -t traffic-rule-monitoring .
```
`docker/sources/MANIFEST.txt` records the branch, commit, and uncommitted changes of every copied repository.

2. Make sure that you are in the root directory of this repository and start the container:
```bash
docker run -it --rm -v $(pwd):/workspace ghcr.io/commonroad/traffic-rule-monitoring/traffic-rule-monitoring:latest /bin/bash
```
The command mounts the current working directory into the container.
Thus, modifications to the code inside the container are also reflected on your machine, and the results remain accessible after the container has stopped.

> **Note:** If you are using Windows, replace `$(pwd)` with `%cd%`.

3. Install the evaluation package inside the container:
```bash
pip install -e .
```
The editable install (`-e`) is required: the scripts locate the scenarios, configurations, and output directory relative to the repository.

> **Note:** You might not have permission to access files created inside the container from the host machine.
> In this case, change the owner of the files using `sudo chown -R $USER <directory>`.

## :gear: Monitor Configurations

The scripts compare the following configurations of the monitor.
Each configuration enables one additional feature.
The code uses the names of the paper (the planner without monitor is called "No monitor"). Former versions of the code used the names in the second column:

| Paper | Code | Connected | Short-circuiting | Reordering | Iterative | Early termination |
|---|---|:-:|:-:|:-:|:-:|:-:|
| – (planner without monitor) | C0 | | | | | |
| Baseline | C1 | | | | | |
| C1 | C2 | ✓ | | | | |
| C2 | C3 | ✓ | ✓ | | | |
| Ours | C4 | ✓ | ✓ | ✓ | | |
| Ours<sup>I</sup> | C5 | ✓ | ✓ | ✓ | ✓ | |
| Ours<sup>E</sup> | C6 | ✓ | ✓ | ✓ | ✓ | ✓ |

The configurations are defined in `src/evaluation/common/config.py`, together with the evaluated rule sets for interstates (R_G1–R_G4, R_I1–R_I5) and intersections (R_G1–R_G4, R_U1–R_U5).
The predicate costs and satisfaction probabilities used for reordering are stored in `configurations/predicates/` (the `*_inverted.yaml` files are used for configurations without reordering).

## :arrow_forward: Replicating the Results from the Paper

All results from the paper can be replicated with the scripts in the root directory of this repository.
All outputs are written to the `output/` directory.

All computation times in the paper were measured using a single thread on an AMD Ryzen 9 9950X CPU with 64 GB RAM.
The scripts with a `--threads` option use one thread by default.
You can increase the number of threads to reduce the total runtime, but the individual computation times will then differ from the paper.
Evaluations exceeding the cut-off time of 20 minutes (`--cutoff`/`--timeout`) and failed evaluations are marked with x in the generated tables and are not part of the medians.

| Script | Results in the paper |
|---|---|
| `00_motivation_examples.py` | Motivating example |
| `01_monitor.py` | Artificial specifications and traces (trace length and reordering evaluation) |
| `02_predicate_eval.py` | Predicate costs and satisfaction probabilities |
| `03_cr_scenario_eval_computation_time.py` | Computation times for evaluating recorded scenarios |
| `04_cr_scenario_eval_visualization.py` | Visualization of the evaluated scenarios (e.g., USA_US101-14_7_T-1) |
| `05_planning_computation_time.py` | Computation times of the rule-compliant motion planner |
| `06_planning_visualization.py` | Planning steps and final trajectories |
| `07_set_based.py` | Set-based prediction: safe distance and left-turn examples |
| `08_carla_traffic_light.py`, `09_carla_yield_sign.py` | Interactive simulation in CARLA |
| `10_set_based_summary.py` | Set-based prediction: statistics over 23 CommonRoad scenarios |

### `00_motivation_examples.py`

Reproduces the figures of the motivating example: the planning example in ZAM_Augmentation-1_1_T-1 and the monitoring example in USA_US101-22_5_T-1.
```bash
python 00_motivation_examples.py
```

### `01_monitor.py`

Evaluates our monitor on artificial specifications and traces: computation time over the trace length, and the influence of reordering for conjunctions and disjunctions.
All parameters (specifications, trace lengths, number of iterations, seed) are defined in `configurations/rv_monitor/evaluation_parameters.yaml`.
To reduce the runtime, decrease `num_iters` or the trace lengths there.
The results are written to `output/monitor`.

The formulas and traces are generated with `gen_fmla` and `gen_log` in `src/evaluation/monitor/exec/`.
These are the generators of the [Hydra/Vydra](https://bitbucket.org/krle/hydra) monitors by Raszyk et al., compiled for Linux x86-64.

If you want to create LaTeX-ready TikZ images, install `tikzplotlib` and set `with_tex: true` in the parameter file:
```bash
pip install "matplotlib<3.6" "tikzplotlib==0.10.1" "webcolors<=1.11.1"
```
Then, run the script:
```bash
python 01_monitor.py
```

### `02_predicate_eval.py`

Measures the computation time and satisfaction probability of every predicate on the provided scenarios.
The script writes the predicate cost files, which are used for reordering, to `output/predicates`.
The files used for the paper are stored in `configurations/predicates`.
```bash
python 02_predicate_eval.py [--threads N] [--step_size 10]
```

### `03_cr_scenario_eval_computation_time.py`

Evaluates the rule compliance of all vehicles in the recorded interstate and intersection scenarios with all configurations.
The table with the median computation times is written to `output/planning/comp_summary.txt`.
```bash
python 03_cr_scenario_eval_computation_time.py [--threads N] [--repetitions 5]
```

### `04_cr_scenario_eval_visualization.py`

Visualizes the evaluated scenarios with rule-compliant (green) and violating (red) vehicles.
The plots are written to `output/planning`.
```bash
python 04_cr_scenario_eval_visualization.py
```

### `05_planning_computation_time.py`

Solves the planning scenarios with the reactive planner using the different configurations and reports the computation times.
The results are written to `output/planning`.
```bash
python 05_planning_computation_time.py [--threads N] [--timeout 1200]
```

### `06_planning_visualization.py`

Plots planning steps and the final trajectory of the planning scenarios with and without the monitor.
The plots are written to `output/planning`.
```bash
python 06_planning_visualization.py
```

### `07_set_based.py`

Evaluates the safe distance rule R_G1 in ZAM_Augmentation-1_1_S-1 and the left-turn rule in DEU_TestTurnLeft-1_1_T-1 using set-based predictions, with and without the monitor.
The plots are written to `output/set_based`.
```bash
python 07_set_based.py
```

### `08_carla_traffic_light.py` and `09_carla_yield_sign.py` (optional)

Run the interactive simulations: approaching a red traffic light and turning right at a T-intersection with a yield sign.
Both scripts require a running CARLA 0.10 server, which is not part of the Docker image.
See the [CommonRoad-CARLA Interface](https://github.com/CommonRoad/commonroad-carla-interface) for setup instructions.
```bash
python 08_carla_traffic_light.py
python 09_carla_yield_sign.py
```

### `10_set_based_summary.py`

Executes one planning cycle with and without the monitor for each set-based CommonRoad scenario in `scenarios/set_based/cr_scenarios` (23 scenarios) and counts the trajectories rejected due to rule violations.
Two scenarios that crash the environment model are skipped, so 23 scenarios are evaluated.
Each run is executed in a separate process.
The results are written to `output/set_based_scenario_eval`.
```bash
python 10_set_based_summary.py [--limit N] [--scenario <scenario_id>]
```

## :wrench: Tools

The `tools/` directory contains helper scripts and additional evaluations that are not required to reproduce the results of the paper.

### `tools/update_image_brightness.py`

CARLA 0.10 does not support changing the sun configuration.
This script brightens the recorded CARLA images via gamma correction.
```bash
python tools/update_image_brightness.py <image_folder> [--output_folder brightened_results] [--gamma 1.1]
```

### `tools/formula_size_eval.py`

Evaluates the computation time of the monitor on artificial specifications over the formula size.
This evaluation is not part of the paper.
The parameters are in the `formula_size_eval` section of `configurations/rv_monitor/evaluation_parameters.yaml`, and the results are written to `output/monitor`.
```bash
python tools/formula_size_eval.py
```

## :floppy_disk: Data

All scenarios are in the [CommonRoad format](https://commonroad.in.tum.de).
The interstate and intersection scenarios with the prefix `USA_US101` and `USA_Peach` are created from the [NGSIM](https://ops.fhwa.dot.gov/trafficanalysistools/ngsim.htm) dataset.
The set-based scenarios are taken from the [CommonRoad benchmark suite](https://commonroad.in.tum.de/scenarios).
Scenarios with the prefix `ZAM` were created manually using the [CommonRoad Scenario Designer](https://commonroad.in.tum.de/tools/scenario-designer).

## :warning: Known Issues

- Computation times depend on the hardware and the system load, so your values might differ from the ones in the paper. The relative differences between the configurations should be similar.
- Each predicate evaluation in `02_predicate_eval.py` has a timeout of 0.5 s.

<!--
## :speech_balloon: Citation

If you use this repository for your research, please cite our paper:
```bibtex
@article{Maierhofer2026,
  author  = {Maierhofer, Sebastian and Althoff, Matthias},
  title   = {Efficient Traffic Rule Monitoring for Rule-Compliant Motion Planning of Automated Vehicles},
  journal = {tbd},
  volume  = {tbd},
  number  = {tbd},
  pages   = {tbd},
  year    = {tbd},
}
```
-->

## :handshake: Acknowledgments

We thank Yannick Ballnath and Valentin Merle for their contribution to the traffic rule monitor implementation.

## :page_facing_up: License

See [LICENSE](LICENSE).
The related repositories listed above have their own licenses.
