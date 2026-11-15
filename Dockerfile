FROM python:3.11-bullseye

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        ca-certificates wget git pkg-config \
        build-essential g++-13 clang ninja-build \
        libomp-dev \
        libboost-all-dev \
        libeigen3-dev \
        libprotobuf-dev protobuf-compiler \
        libyaml-cpp-dev \
        libspdlog-dev \
        librange-v3-dev \
        libgtest-dev libgmock-dev doctest-dev \
        libgl1 \
        default-jdk && \
    rm -rf /var/lib/apt/lists/*

# Install newer version of CMake than provided by the standard repos
ARG CMAKE_VERSION="4.0.3"
RUN wget "https://github.com/Kitware/CMake/releases/download/v${CMAKE_VERSION}/cmake-${CMAKE_VERSION}-Linux-x86_64.sh" \
    -q -O /tmp/cmake-install.sh && \
    chmod u+x /tmp/cmake-install.sh && \
    mkdir /opt/cmake && \
    /tmp/cmake-install.sh --skip-license --prefix=/opt/cmake && \
    rm /tmp/cmake-install.sh
ENV PATH="/opt/cmake/bin:${PATH}"

# Versions of the CommonRoad tools used for the results in the paper.
# commonroad-monitor builds and installs commonroad-cpp (environment model) and rv-monitors at the versions it pins.
ARG COMMONROAD_GITHUB="https://github.com/CommonRoad"
ARG COMMONROAD_MONITOR_REF="TODO-release-tag"
ARG REACTIVE_PLANNER_REF="TODO-release-tag"
ARG COMMONROAD_PREDICTION_REF="TODO-release-tag"
ARG COMMONROAD_CARLA_INTERFACE_REF="TODO-release-tag"

RUN pip install --no-cache-dir \
        "commonroad_monitor @ git+${COMMONROAD_GITHUB}/commonroad-monitor.git@${COMMONROAD_MONITOR_REF}" && \
    pip install --no-cache-dir \
        "commonroad-reactive-planner @ git+${COMMONROAD_GITHUB}/commonroad-reactive-planner.git@${REACTIVE_PLANNER_REF}" \
        "commonroad-prediction @ git+${COMMONROAD_GITHUB}/commonroad-prediction.git@${COMMONROAD_PREDICTION_REF}" \
        "commonroad-carla-interface @ git+${COMMONROAD_GITHUB}/commonroad-carla-interface.git@${COMMONROAD_CARLA_INTERFACE_REF}"

# Install the remaining (public) dependencies of the evaluation package.
# The repository itself is mounted to /workspace at runtime and installed with `pip install .` (see README).
COPY pyproject.toml README.md /tmp/evaluation/
COPY src /tmp/evaluation/src
RUN pip install --no-cache-dir /tmp/evaluation && pip uninstall -y evaluation && rm -rf /tmp/evaluation

WORKDIR /workspace
