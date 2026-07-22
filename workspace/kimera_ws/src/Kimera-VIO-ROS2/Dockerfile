# syntax=docker/dockerfile:experimental
# Example: export DOCKER_BUILDKIT=1
# https://github.com/moby/buildkit/blob/master/frontend/dockerfile/docs/experimental.md
# docker build --progress=plain --tag ruffsl/kimera_vio_ros2 .
ARG FROM_IMAGE=osrf/ros2:nightly
ARG UNDERLAY_WS=/opt/ros/underlay_ws
ARG OVERLAY_WS=/opt/ros/overlay_ws
ARG WRAPPER_WS=/opt/ros/wrapper_ws

# multi-stage for caching
FROM $FROM_IMAGE AS cacher

# clone underlay source
ARG UNDERLAY_WS
WORKDIR $UNDERLAY_WS/src
COPY ./install/underlay.repos ../
RUN vcs import ./ < ../underlay.repos && \
    find ./ -name ".git" | xargs rm -rf

# copy overlay source
ARG OVERLAY_WS
WORKDIR $OVERLAY_WS/src
COPY ./install/overlay.repos ../
RUN vcs import ./ < ../overlay.repos && \
    find ./ -name ".git" | xargs rm -rf

# copy wrapper source
ARG WRAPPER_WS
WORKDIR $WRAPPER_WS/src
COPY ./ ./MIT-SPARK/Kimera-VIO-ROS2
COPY ./install/wrapper.repos ../
RUN vcs import ./ < ../wrapper.repos && \
    find ./ -name ".git" | xargs rm -rf

# copy manifests for caching
WORKDIR /opt
RUN mkdir -p /tmp/opt && \
    find ./ -name "package.xml" | \
      xargs cp --parents -t /tmp/opt && \
    find ./ -name "COLCON_IGNORE" | \
      xargs cp --parents -t /tmp/opt || true

# multi-stage for building
FROM $FROM_IMAGE AS builder

# edit apt for caching
RUN cp /etc/apt/apt.conf.d/docker-clean /etc/apt/ && \
    echo 'Binary::apt::APT::Keep-Downloaded-Packages "true";' \
      > /etc/apt/apt.conf.d/docker-clean

# install CI dependencies
RUN --mount=type=cache,target=/var/cache/apt \
    --mount=type=cache,target=/var/lib/apt \
    apt-get update && apt-get install -q -y \
      ccache \
      lcov \
      libboost-all-dev

# install underlay dependencies
ARG UNDERLAY_WS
WORKDIR $UNDERLAY_WS
COPY --from=cacher /tmp/$UNDERLAY_WS/src ./src
RUN --mount=type=cache,target=/var/cache/apt \
    --mount=type=cache,target=/var/lib/apt \
    . /opt/ros/$ROS_DISTRO/setup.sh && \
    apt-get update && apt-get install -q -y libboost-all-dev libgflags-dev libgoogle-glog-dev libtbb-dev && \
    rosdep install -q -y \
      --from-paths src \
      --ignore-src

# build underlay source
COPY --from=cacher $UNDERLAY_WS/src ./src
RUN python3 -c "c = open('./src/borglab/gtsam/CMakeLists.txt').read(); c = c.replace('find_package(TBB 4.4 COMPONENTS tbb tbbmalloc)', 'if(GTSAM_WITH_TBB)\n  find_package(TBB 4.4 COMPONENTS tbb tbbmalloc)\nendif()'); open('./src/borglab/gtsam/CMakeLists.txt', 'w').write(c)"
RUN python3 -c "import os; fn = './src/borglab/gtsam/gtsam/base/Matrix.h'; c = open(fn).read(); open(fn, 'w').write(c.replace('#include <boost/serialization/', '#include <boost/serialization/version.hpp>\n#include <boost/serialization/library_version_type.hpp>\n#include <boost/serialization/', 1)); other = ['./src/borglab/gtsam/gtsam/base/FastList.h', './src/borglab/gtsam/gtsam/base/FastSet.h', './src/borglab/gtsam/gtsam/base/FastMap.h', './src/borglab/gtsam/gtsam/base/serialization.h']; [open(f, 'w').write(c.replace('#include <boost/serialization/', '#include <gtsam/base/Matrix.h>\n#include <boost/serialization/version.hpp>\n#include <boost/serialization/library_version_type.hpp>\n#include <boost/serialization/', 1)) for f in other if os.path.exists(f) for c in [open(f).read()] if 'library_version_type' not in c]"
ARG UNDERLAY_MIXINS="release ccache"
RUN --mount=type=cache,target=/root/.ccache \
    . /opt/ros/$ROS_DISTRO/setup.sh && \
    colcon build \
      --symlink-install \
      --mixin $UNDERLAY_MIXINS \
      --cmake-args \
        --no-warn-unused-cli \
        -DCMAKE_CXX_STANDARD=14 \
        -DGTSAM_USE_SYSTEM_EIGEN=ON \
        -DGTSAM_BUILD_TESTS=OFF \
        -DGTSAM_BUILD_EXAMPLES_ALWAYS=OFF \
        -DGTSAM_BUILD_UNSTABLE=ON \
        -DGTSAM_POSE3_EXPMAP=ON \
        -DGTSAM_ROT3_EXPMAP=ON \
        -DGTSAM_WITH_TBB=OFF \
        -DCMAKE_POLICY_VERSION_MINIMUM=3.5
      # --event-handlers console_direct+


# install overlay dependencies
ARG OVERLAY_WS
WORKDIR $OVERLAY_WS
COPY --from=cacher /tmp/$OVERLAY_WS/src ./src
RUN --mount=type=cache,target=/var/cache/apt \
    --mount=type=cache,target=/var/lib/apt \
    . $UNDERLAY_WS/install/setup.sh && \
    apt-get update && rosdep install -q -y \
      --from-paths src \
        $UNDERLAY_WS/src \
      --ignore-src

# build overlay source
COPY --from=cacher $OVERLAY_WS/src ./src
RUN python3 -c "fn = './src/MIT-SPARK/Kimera-VIO/CMakeLists.txt'; c = open(fn).read(); open(fn, 'w').write(c.replace('DBoW2_INCLUDE_DIRS}/..', 'DBoW2_INCLUDE_DIRS}'))"
RUN python3 -c "open('./src/MIT-SPARK/Kimera-VIO/package.xml', 'w').write('<?xml version=\"1.0\"?>\\n<package format=\"3\">\\n  <name>kimera_vio</name>\\n  <version>1.0.0</version>\\n  <description>Kimera-VIO package</description>\\n  <maintainer email=\"terrence@todo.todo\">Terrence</maintainer>\\n  <license>BSD</license>\\n  <buildtool_depend>cmake</buildtool_depend>\\n  <build_depend>kimera_rpgo</build_depend>\\n  <build_depend>gtsam</build_depend>\\n  <build_depend>opengv</build_depend>\\n  <build_depend>dbow2</build_depend>\\n  <export>\\n    <build_type>cmake</build_type>\\n  </export>\\n</package>\\n')"
COPY ./patch_yaml_parser.py ./patch_yaml_parser.py
RUN python3 ./patch_yaml_parser.py
ARG OVERLAY_MIXINS="release ccache"
RUN --mount=type=cache,target=/root/.ccache \
    . $UNDERLAY_WS/install/setup.sh && \
    colcon build \
      --symlink-install \
      --mixin $OVERLAY_MIXINS \
      --cmake-args \
        --no-warn-unused-cli \
        -DCMAKE_POLICY_VERSION_MINIMUM=3.5 \
        -DCMAKE_CXX_STANDARD=14 \
        -DBUILD_TESTS=OFF \
        -DCMAKE_CXX_FLAGS="\
          -Wno-comment \
          -Wno-parentheses \
          -Wno-reorder \
          -Wno-sign-compare \
          -Wno-unused-but-set-variable \
          -Wno-unused-function \
          -Wno-unused-parameter \
          -Wno-unused-value \
          -Wno-unused-variable"

# install wrapper dependencies
ARG WRAPPER_WS
WORKDIR $WRAPPER_WS
COPY --from=cacher /tmp/$WRAPPER_WS/src ./src
RUN --mount=type=cache,target=/var/cache/apt \
    --mount=type=cache,target=/var/lib/apt \
    . $OVERLAY_WS/install/setup.sh && \
    export DEBIAN_FRONTEND=noninteractive && \
    apt-get update && rosdep install -q -y \
      --from-paths src \
        $UNDERLAY_WS/src \
        $OVERLAY_WS/src \
      --ignore-src

# build wrapper source
COPY --from=cacher $WRAPPER_WS/src ./src
ARG WRAPPER_MIXINS="release ccache"
RUN --mount=type=cache,target=/root/.ccache \
    . $OVERLAY_WS/install/setup.sh && \
    find /opt/ros/overlay_ws/install -maxdepth 3 || true && \
    echo "CMAKE_PREFIX_PATH is $CMAKE_PREFIX_PATH" && \
    export CMAKE_PREFIX_PATH="/opt/ros/overlay_ws/install/kimera_vio:/opt/ros/overlay_ws/install/kimera_rpgo:$CMAKE_PREFIX_PATH" && \
    echo "Modified CMAKE_PREFIX_PATH is $CMAKE_PREFIX_PATH" && \
    colcon build \
      --symlink-install \
      --mixin $WRAPPER_MIXINS \
      --cmake-args \
        --no-warn-unused-cli \
        -DCMAKE_CXX_STANDARD=14 \
        -DCMAKE_CXX_FLAGS="\
          -Wno-comment \
          -Wno-sign-compare \
          -Wno-unused-value \
          -Wno-unused-variable \
          -Wno-unused-but-set-variable \
          -Wno-reorder \
          -Wno-parentheses \
          -Wno-unused-parameter"
      # --event-handlers console_direct+

# restore apt for docker
RUN mv /etc/apt/docker-clean /etc/apt/apt.conf.d/ && \
    rm -rf /var/lib/apt/lists/

# source wrapper from entrypoint
ENV WRAPPER_WS $WRAPPER_WS
RUN sed --in-place \
      's|^source .*|source "$WRAPPER_WS/install/setup.bash"|' \
      /ros_entrypoint.sh
