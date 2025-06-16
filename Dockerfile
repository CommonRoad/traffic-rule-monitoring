###############
# Build image #
###############
FROM python:3.11-bullseye AS build

RUN apt-get update && \
    apt-get install -y \
        ca-certificates wget git pkg-config \
        build-essential g++-13 clang ninja-build \
        clang-format-13 clang-tidy-13 \
        gcovr doxygen graphviz cppcheck \
        libomp-dev \
        libboost-all-dev \
        libeigen3-dev \
        libprotobuf-dev protobuf-compiler \
        libyaml-cpp-dev \
        libspdlog-dev \
        libgtest-dev \
        librange-v3-dev \
        libgl1 \
        libgtest-dev libgmock-dev \
        doctest-dev \
        default-jdk && \
    apt-get update && \
    apt-get install -y  && \
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

RUN pip install --no-cache-dir pipx && pipx ensurepath && pipx install poetry
ENV PATH="/root/.local/bin:${PATH}"

COPY . .
RUN poetry install -v

WORKDIR /workspace


