FROM ros:humble-perception

ENV DEBIAN_FRONTEND=noninteractive

# Install dependencies for Pangolin and ORB_SLAM3
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    git \
    wget \
    unzip \
    pkg-config \
    libopencv-dev \
    libegl1-mesa-dev \
    libglew-dev \
    libpython3-dev \
    libssl-dev \
    python3-pip \
    python3-colcon-common-extensions \
    libboost-system-dev \
    libboost-serialization-dev \
    libepoxy-dev \
    libwayland-dev \
    libxkbcommon-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Pangolin
WORKDIR /opt
RUN git clone https://github.com/stevenlovegrove/Pangolin.git && \
    cd Pangolin && \
    mkdir build && cd build && \
    cmake .. -DCMAKE_BUILD_TYPE=Release && \
    make -j2 && \
    make install



# Clone ORB_SLAM3 (using the fork mentioned in the ROS2 wrapper)
WORKDIR /opt
RUN git clone https://github.com/zang09/ORB-SLAM3-STEREO-FIXED.git ORB_SLAM3 && \
    cd ORB_SLAM3 && \
    sed -i 's/make -j/make -j2/g' build.sh && \
    chmod +x build.sh

# The build.sh uses make -j, which might fail on memory constrained systems, 
# but inside Docker we use -j2
WORKDIR /opt/ORB_SLAM3
RUN ./build.sh && \
    cd Thirdparty/Sophus/build && \
    make install

# Clone and build the ROS 2 Wrapper
RUN mkdir -p /root/ros2_ws/src
WORKDIR /root/ros2_ws/src
RUN git clone -b humble https://github.com/zang09/ORB_SLAM3_ROS2.git orbslam3

WORKDIR /root/ros2_ws
# Fix CMakePaths in ORB_SLAM3_ROS2 to point to /opt/ORB_SLAM3
RUN sed -i 's|set(ORB_SLAM3_ROOT_DIR .*)|set(ORB_SLAM3_ROOT_DIR "/opt/ORB_SLAM3")|g' src/orbslam3/CMakeModules/FindORB_SLAM3.cmake

# Build ROS2 wrapper with safe 2 workers (prevents GCC RAM explosion)
RUN /bin/bash -c "source /opt/ros/humble/setup.bash && \
    colcon build --symlink-install --parallel-workers 2"

# Fix shared library linking for Pangolin
ENV LD_LIBRARY_PATH=/usr/local/lib:$LD_LIBRARY_PATH
RUN ldconfig

# Add sourcing to bashrc
RUN echo "source /opt/ros/humble/setup.bash" >> /root/.bashrc && \
    echo "source /root/ros2_ws/install/setup.bash" >> /root/.bashrc

# Install mcap plugin for ros2 bag play
RUN apt-get update && apt-get install -y ros-humble-rosbag2-storage-mcap && rm -rf /var/lib/apt/lists/*

WORKDIR /root/ros2_ws
