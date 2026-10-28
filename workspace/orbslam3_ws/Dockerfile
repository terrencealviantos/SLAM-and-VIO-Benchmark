FROM slam-base:latest

ENV DEBIAN_FRONTEND=noninteractive

# Install dependencies for Pangolin and ORB_SLAM3
RUN apt-get update && apt-get install -y \
    libepoxy-dev \
    libwayland-dev \
    libxkbcommon-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Pangolin v0.6 using single-threaded make
WORKDIR /opt
RUN git clone --branch v0.6 --depth 1 https://github.com/stevenlovegrove/Pangolin.git && \
    cd Pangolin && \
    mkdir build && cd build && \
    cmake .. -DCMAKE_BUILD_TYPE=Release -DBUILD_PANGOLIN_PYTHON=OFF -DBUILD_EXAMPLES=OFF && \
    make -j1 && \
    make install && \
    ldconfig

# Clone ORB_SLAM3
WORKDIR /opt
RUN git clone https://github.com/zang09/ORB-SLAM3-STEREO-FIXED.git ORB_SLAM3

# Build Thirdparty with strictly single-threaded make to minimize RAM
WORKDIR /opt/ORB_SLAM3
RUN cd Thirdparty/DBoW2 && mkdir -p build && cd build && cmake .. -DCMAKE_BUILD_TYPE=Release && make -j1 && \
    cd /opt/ORB_SLAM3/Thirdparty/g2o && mkdir -p build && cd build && cmake .. -DCMAKE_BUILD_TYPE=Release && make -j1 && \
    cd /opt/ORB_SLAM3/Thirdparty/Sophus && mkdir -p build && cd build && cmake .. -DCMAKE_BUILD_TYPE=Release && make -j1 && make install && \
    cd /opt/ORB_SLAM3/Vocabulary && tar -xf ORBvoc.txt.tar.gz

# Build core ORB_SLAM3 library and examples
RUN cd /opt/ORB_SLAM3 && mkdir -p build && cd build && cmake .. -DCMAKE_BUILD_TYPE=Release && make -j1

# Clone and build the ROS 2 Wrapper
RUN mkdir -p /root/ros2_ws/src
WORKDIR /root/ros2_ws/src
RUN git clone -b humble https://github.com/zang09/ORB_SLAM3_ROS2.git orbslam3 && \
    sed -i 's|set(ORB_SLAM3_ROOT_DIR .*)|set(ORB_SLAM3_ROOT_DIR "/opt/ORB_SLAM3")|g' orbslam3/CMakeModules/FindORB_SLAM3.cmake

# Build ROS2 wrapper
WORKDIR /root/ros2_ws
RUN /bin/bash -c "source /opt/ros/humble/setup.bash && \
    MAKEFLAGS='-j1' colcon build --symlink-install --parallel-workers 1"

# Fix shared library linking for Pangolin and ORB_SLAM3
RUN echo '/usr/local/lib' > /etc/ld.so.conf.d/orbslam3.conf && \
    echo '/opt/ORB_SLAM3/lib' >> /etc/ld.so.conf.d/orbslam3.conf && \
    echo '/opt/ORB_SLAM3/Thirdparty/DBoW2/lib' >> /etc/ld.so.conf.d/orbslam3.conf && \
    echo '/opt/ORB_SLAM3/Thirdparty/g2o/lib' >> /etc/ld.so.conf.d/orbslam3.conf && \
    ldconfig

ENV LD_LIBRARY_PATH=/usr/local/lib:/opt/ORB_SLAM3/lib:/opt/ORB_SLAM3/Thirdparty/DBoW2/lib:/opt/ORB_SLAM3/Thirdparty/g2o/lib:$LD_LIBRARY_PATH

# Add sourcing to bashrc
RUN echo "source /opt/ros/humble/setup.bash" >> /root/.bashrc && \
    echo "source /root/ros2_ws/install/setup.bash" >> /root/.bashrc

WORKDIR /root/ros2_ws
