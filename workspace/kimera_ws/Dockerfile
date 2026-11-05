# Kimera-VIO (latest official master) for the benchmark.
#
# Based on the official MIT-SPARK/Kimera-VIO Dockerfile_20_04, with every dependency pinned
# to the commit that file currently pulls. Differences from the official file:
#   - builds Kimera-VIO itself (the official file stops after the dependencies)
#   - applies kimera_benchmark.patch (see below)
#   - JOBS parallel compile jobs (default 3) instead of $(nproc): GTSAM uses ~2 GB per
#     job, 16 jobs exhaust RAM on a 22 GB laptop
#   - deletes build folders after install, skips Kimera-VIO-Evaluation (not needed)
#
# kimera_benchmark.patch (88 lines, 4 files):
#   1. EurocDataProvider: a dataset without state_groundtruth_estimate0/sensor.yaml runs
#      without ground truth (as Kimera-VIO did in 2020) instead of aborting.
#   2. PipelineModule::spin(): writes kimera_scoped_timing.csv with the start/end time of
#      every module execution (include/kimera-vio/utils/ScopedTiming.h).
#   3. VioBackend: debug timers used whole seconds (always 0); now microseconds.
#
# Build:  docker build -t kimera-latest:ce8c59b workspace/kimera_ws
FROM ubuntu:20.04

ARG JOBS=3
ENV DEBIAN_FRONTEND=noninteractive
WORKDIR /opt/kimera

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      build-essential cmake gfortran git ca-certificates unzip \
      libatlas-base-dev libboost-all-dev libeigen3-dev libgflags-dev libgoogle-glog-dev \
      libmetis-dev libopencv-dev libopencv-contrib-dev libtbb-dev pkg-config && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# GTSAM 4.2 (same CMake options as the official file)
RUN git clone https://github.com/borglab/gtsam.git && cd gtsam && \
    git checkout 4f66a491ffc83cf092d0d818b11dc35135521612 && \
    mkdir build && cd build && \
    cmake -DCMAKE_INSTALL_PREFIX=/usr/local \
          -DGTSAM_BUILD_WITH_MARCH_NATIVE=OFF -DGTSAM_BUILD_TESTS=OFF \
          -DGTSAM_BUILD_EXAMPLES_ALWAYS=OFF -DCMAKE_BUILD_TYPE=Release \
          -DGTSAM_BUILD_UNSTABLE=ON -DGTSAM_POSE3_EXPMAP=ON -DGTSAM_ROT3_EXPMAP=ON \
          -DGTSAM_TANGENT_PREINTEGRATION=OFF -DGTSAM_USE_SYSTEM_EIGEN=ON \
          -DGTSAM_USE_SYSTEM_METIS=ON .. && \
    make -j${JOBS} install && cd /opt/kimera && rm -rf gtsam

# OpenGV (Kimera's fork, march=native disabled)
RUN git clone https://github.com/marcusabate/opengv && cd opengv && \
    git checkout 984e0d76a19e0afa9435f03adbc8aaccc9f92c23 && \
    git apply march_native_disable.patch && \
    mkdir build && cd build && \
    cmake -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=/usr/local .. && \
    make -j${JOBS} install && cd /opt/kimera && rm -rf opengv

# Kimera-VIO source (needed here for the DBoW2 patch; built last)
RUN git clone https://github.com/MIT-SPARK/Kimera-VIO.git && cd Kimera-VIO && \
    git checkout ce8c59b7b273ab5ac29db7e5572e1623760e19c7

# DBoW2 with Kimera's vocabulary patch
RUN git clone https://github.com/dorian3d/DBoW2.git && cd DBoW2 && \
    git checkout 3924753db6145f12618e7de09b7e6b258db93c6e && \
    git apply /opt/kimera/Kimera-VIO/.patches/fix_vocab.patch && \
    mkdir build && cd build && cmake .. && \
    make -j${JOBS} install && cd /opt/kimera && rm -rf DBoW2

# Kimera-RPGO
RUN git clone https://github.com/MIT-SPARK/Kimera-RPGO.git && cd Kimera-RPGO && \
    git checkout d28b4df0570d642a2bb00e511344ce1110f87519 && \
    mkdir build && cd build && cmake .. && \
    make -j${JOBS} install && cd /opt/kimera && rm -rf Kimera-RPGO

# Kimera-VIO + benchmark patch (last layer, so a patch change only rebuilds this)
COPY kimera_benchmark.patch /opt/kimera/kimera_benchmark.patch
RUN cd Kimera-VIO && git apply /opt/kimera/kimera_benchmark.patch && \
    mkdir build && cd build && \
    cmake -DCMAKE_BUILD_TYPE=Release .. && \
    make -j${JOBS} stereoVIOEuroc && \
    ls -la stereoVIOEuroc ../vocabulary/ORBvoc.yml

ENV LD_LIBRARY_PATH=/usr/local/lib:/opt/kimera/Kimera-VIO/build
WORKDIR /
