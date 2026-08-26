#!/bin/bash
# ==============================================================================
# install_cuvslam_dependencies.sh
# One-click host setup script for NVIDIA cuVSLAM / Isaac ROS
# Installs: Docker, NVIDIA Drivers, NVIDIA Container Toolkit
# ==============================================================================

set -e

if [ "$EUID" -ne 0 ]; then
  echo "[!] Please run this script with sudo: sudo bash $0"
  exit 1
fi

TARGET_USER="${SUDO_USER:-$USER}"

echo "=========================================================="
echo " 1/4: Installing Docker Engine..."
echo "=========================================================="
apt-get update
apt-get install -y ca-certificates curl gnupg lsb-release docker.io

# Add user to docker group
usermod -aG docker "$TARGET_USER"
systemctl enable docker
systemctl start docker
echo "[✔] Docker installed and user '$TARGET_USER' added to docker group."

echo "=========================================================="
echo " 2/4: Installing NVIDIA Driver..."
echo "=========================================================="
# Check if nvidia-smi is already functional
if command -v nvidia-smi &>/dev/null && nvidia-smi &>/dev/null; then
    echo "[✔] NVIDIA driver is already installed and loaded."
else
    echo "Installing nvidia-driver-535..."
    apt-get install -y nvidia-driver-535 || apt-get install -y nvidia-driver-550
    echo "[✔] NVIDIA driver installed."
    echo "[!] NOTE: If this is the first time installing the driver, a system reboot (sudo reboot) may be needed to load kernel modules."
fi

echo "=========================================================="
echo " 3/4: Installing NVIDIA Container Toolkit..."
echo "=========================================================="
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | gpg --dearmor --yes -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
  sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
  tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

apt-get update
apt-get install -y nvidia-container-toolkit

echo "=========================================================="
echo " 4/4: Configuring Docker for NVIDIA GPU Passthrough..."
echo "=========================================================="
nvidia-ctk runtime configure --runtime=docker
systemctl restart docker

echo "=========================================================="
echo " Setup Completed Successfully!"
echo "=========================================================="
echo "Next steps:"
echo " 1. If you just installed the NVIDIA driver, reboot once:"
echo "    sudo reboot"
echo " 2. Launch cuVSLAM:"
echo "    cd /home/boris/SLAM-and-VIO-Benchmark/workspace"
echo "    bash run_cuvslam.sh"
echo "=========================================================="
