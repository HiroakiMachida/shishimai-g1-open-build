FROM ros:foxy-ros-base@sha256:34fbe32f5b1cd3eb25f6becaaa1d293bad754d64c31d96e638e4b30ed82f9f8e
SHELL ["/bin/bash", "-c"]
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential cmake python3-pip python3-colcon-common-extensions \
    ros-foxy-rosidl-default-generators ros-foxy-rmw-fastrtps-cpp ros-foxy-std-srvs \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /submission
COPY runner/him_safety_interfaces /submission/interfaces
RUN source /opt/ros/foxy/setup.bash && colcon build --base-paths interfaces --packages-select him_safety_interfaces
# Foxy uses Python 3.8. This supported inference release consumes the same ONNX.
RUN python3 -m pip install --no-cache-dir numpy==1.24.4 onnxruntime==1.16.3
COPY policy.py /submission/policy.py
COPY vendor /submission/vendor
COPY models /submission/models
COPY assets/g1_profile.json /submission/assets/g1_profile.json
COPY runner/ros_policy.py runner/entrypoint.sh /submission/
ENV OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1
ARG SOURCE_COMMIT=unknown
LABEL org.opencontainers.image.source="https://github.com/HiroakiMachida/shishimai-g1-open-build" \
      org.opencontainers.image.revision=$SOURCE_COMMIT
ENTRYPOINT ["/bin/bash", "/submission/entrypoint.sh"]
