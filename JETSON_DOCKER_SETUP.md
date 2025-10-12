# Jetson Docker Setup (Recommended)

## Why Docker?

The NVIDIA PyTorch container solves:
- ✅ CUDA support out of the box
- ✅ numpy compatibility issues
- ✅ All dependencies pre-installed
- ✅ Optimized for Jetson hardware

## Quick Setup

### 1. Install Docker on Jetson (if not already installed)

```bash
# Install Docker
sudo apt-get update
sudo apt-get install -y docker.io docker-compose

# Add user to docker group
sudo usermod -aG docker $USER

# Install NVIDIA Container Toolkit
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
    sudo tee /etc/apt/sources.list.d/nvidia-docker.list

sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit
sudo systemctl restart docker

# Log out and back in for group to take effect
```

### 2. Copy Files to Jetson

From your Mac:

```bash
# Copy docker-compose file
scp docker-compose.jetson.yml kronos@192.168.0.105:~/homepi/docker-compose.yml

# Copy inference server
scp jetson_inference_server.py kronos@192.168.0.105:~/homepi/
```

### 3. Start Container on Jetson

```bash
cd ~/homepi

# Pull the NVIDIA PyTorch image (this will take a few minutes)
docker pull nvcr.io/nvidia/pytorch:24.09-py3

# Start the container
docker-compose up -d

# View logs
docker-compose logs -f
```

You should see:
```
✓ CUDA available: Orin
✓ Model loaded successfully
Starting Flask server on http://0.0.0.0:5001
```

### 4. Test from Raspberry Pi

```bash
cd ~/homepi
python3 object_detector.py
```

## Container Management

```bash
# Start container
docker-compose up -d

# Stop container
docker-compose down

# View logs
docker-compose logs -f

# Restart container
docker-compose restart

# Check status
docker-compose ps
```

## Auto-Start on Boot

```bash
# Enable Docker to start on boot
sudo systemctl enable docker

# Container will auto-restart (restart: unless-stopped in docker-compose.yml)
```

## Troubleshooting

### Permission denied connecting to Docker

```bash
# Add user to docker group
sudo usermod -aG docker $USER

# Log out and back in, or use:
newgrp docker
```

### NVIDIA runtime not found

```bash
# Install NVIDIA Container Toolkit
sudo apt-get install -y nvidia-container-toolkit
sudo systemctl restart docker
```

### Container won't start

```bash
# Check logs
docker-compose logs

# Check Docker is running
sudo systemctl status docker

# Check NVIDIA runtime
docker run --rm --gpus all nvidia/cuda:11.0-base nvidia-smi
```

### Port 5001 already in use

```bash
# Find process using port
sudo lsof -i :5001

# Kill it or change port in docker-compose.yml
```

## Performance

Expected inference times with CUDA:
- **YOLOv5s**: 10-15ms per frame
- **YOLOv5m**: 20-25ms per frame

## Model Options

Edit `jetson_inference_server.py` line 63:

```python
# Faster (smaller)
model = torch.hub.load('ultralytics/yolov5', 'yolov5n')  # Nano
model = torch.hub.load('ultralytics/yolov5', 'yolov5s')  # Small (default)

# More accurate (slower)
model = torch.hub.load('ultralytics/yolov5', 'yolov5m')  # Medium
model = torch.hub.load('ultralytics/yolov5', 'yolov5l')  # Large
```

## Summary

Using Docker with NVIDIA's official PyTorch container is the **easiest and most reliable** way to run AI inference on Jetson Orin. No dependency conflicts, full CUDA support, and optimized performance!

