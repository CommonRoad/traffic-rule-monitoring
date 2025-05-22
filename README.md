# Runtime Verification of Motion Planners Using Formalized Traffic Rules – Evaluation Scripts

This repository contains the evaluation scripts for the paper "Runtime Verification of Motion Planners Using Formalized Traffic Rules".

<img src="assets/img_readme.png" alt="experiment" width="900"/>

> Snapshot from deploying our approach for traffic-rule compliant motion planning in real-world test drives. 

## :file_folder: Overview

The repository contains the following files and directories:
```tree
.
├── configurations/             # Contains the configuration files
│
├── scenarios/                  # Contains the CommonRoad scenarios
│   ├── motivating_example/     # Scenarios used in the motivating example
│   ├── test_drives/            # Scenarios generated from the test drives
│
├── src/                        # Contains the source code for the experiments and the evaluation
│
├── *.py files                  # Main scripts for the evaluation: see below for details
.
```


## :computer: Getting Started

1. Pull the Docker image `no-more-traffic-tickets` from the GitHub container registry (Docker may require `sudo` root privileges if your user is not in the `docker` group):
```bash
docker pull ghcr.io/commonroad/no-more-traffic-tickets/no-more-traffic-tickets:latest
```

2. After pulling the image, make sure that you are in the root directory of the repository (the directory containing this file) and start the container with:
```bash
docker run -it --rm -v $(pwd):/workspace ghcr.io/commonroad/no-more-traffic-tickets/no-more-traffic-tickets:latest /bin/bash
```
The command above mounts the current working directory into the Docker container.
Thus, modifications to the code from inside the container will also be reflected on your local machine.
Moreover, it allows you to access the results even after the container has stopped.

> **Note:** If you are using Windows, you have to replace `$(pwd)` by `%cd%`.

3. Install the evaluation Python package in the Docker container:
```bash
pip install .
```

If the package is installed successfully, you can run the experiments as described [below](#replicating-the-results-from-the-paper).

> **Note:** It can happen that you do not have permissions to access the files created inside the container from the host machine.
> In this case, you can change the owner of the files using `sudo chown -R $USER <directory>`.

## :arrow_forward: Replicating the Results from the Paper

All results from the paper can be replicated with the evaluation scripts in this repository.
We describe the purpose of each script in detail.

### `motivating_example.py`

This script reproduces the figures for the motivating example.
All plots are written to the `output/plots` directory.
You can run the script as follows
```bash
python motivating_examples.py
```

### `evaluate_runtimes.py`

This script evaluates and compares the runtimes of our approach.
The results are written to the `output/runtimes` directory.
You can run the script as follows
```bash
python evaluate_runtimes.py
```

### `test_drives_monitor.py`

This script runs the traffic rule monitor on the CommonRoad scenarios generated from the test drives.
For each relevant rule, it reports whether the rule was satisfied or violated.
You can run the script as follows
```bash
python test_drives_monitor.py
```

### `test_drives_visualization.py`

This script recreates the plots of the CommonRoad scenarios generated from the test drives that are shown in the paper.
All plots are written to the `output/plots` directory.
You can run the script as follows
```bash
python test_drives_visualization.py
```


## :speech_balloon: Citation
```
@article{Althoff2025xx
  author = {Althoff, Matthias and Maierhofer, Sebastian and Würsching, Gerald and Lin, Yuanfei and Lercher, Florian and Stolz, Roland},
  title = {No More Traffic Tickets: A Tutorial to Ensure Traffic-Rule Compliance of Automated Vehicles},
  journal = {Proceedings of the IEEE},
  volume = {tbd},
  number = {tbd},
  pages = {tbd},
  year={2025},
}
```
