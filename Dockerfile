FROM python:3.11-trixie

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

# Third-party Python packages, pinned to the versions used for the results in the paper.
COPY docker/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt && rm /tmp/requirements.txt

# CommonRoad tools, built from the source code in docker/sources/ (created by docker/prepare_sources.sh,
# see docker/sources/MANIFEST.txt for the exact versions).
# All of them are installed with --no-deps: their metadata references each other via git URLs, which pip would
# otherwise try to fetch. Their third-party dependencies come from docker/requirements.txt.
# The source copies contain no .git directory, so the version that setuptools_scm would derive from git is replaced
# by the commit hash recorded in .git-commit.
COPY docker/sources /opt/commonroad
WORKDIR /opt/commonroad
RUN for pkg in commonroad-io environment-model rv-monitors; do \
        SETUPTOOLS_SCM_PRETEND_VERSION="0+g$(cat ${pkg}/.git-commit)" \
            pip install --no-cache-dir --no-deps ./${pkg} || exit 1; \
    done
# commonroad-monitor compiles the environment model and rv-monitors as CMake subprojects.
# It must use the same sources as the crcpp package installed above, otherwise the C++ ABI does not match.
RUN SETUPTOOLS_SCM_PRETEND_VERSION="0+g$(cat commonroad-monitor/.git-commit)" \
    pip install --no-cache-dir --no-deps \
        --config-settings=cmake.define.FETCHCONTENT_SOURCE_DIR_ENVIRONMENTMODEL=/opt/commonroad/environment-model \
        --config-settings=cmake.define.FETCHCONTENT_SOURCE_DIR_RVMONITORS=/opt/commonroad/rv-monitors \
        ./commonroad-monitor
RUN pip install --no-cache-dir --no-deps \
        ./commonroad-velocity-planner \
        ./reactive-planner \
        ./commonroad-prediction \
        ./commonroad-scenario-designer \
        ./commonroad-carla-interface

# Install the remaining (public) dependencies of the evaluation package.
# The repository itself is mounted to /workspace at runtime and installed with `pip install -e .` (see README).
COPY pyproject.toml README.md /tmp/evaluation/
COPY src /tmp/evaluation/src
RUN pip install --no-cache-dir /tmp/evaluation && pip uninstall -y evaluation && rm -rf /tmp/evaluation

WORKDIR /workspace
