# Use a base image with CUDA support
FROM nvidia/cuda:11.6.2-devel-ubuntu20.04

# Set the working directory
WORKDIR /workspace

# Install dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    g++ \
    git \
    curl \
    vim \
    python3 \
    python3-pip \
    mysql-client \
    libmysqlclient-dev \
    && apt-get clean

RUN apt-get install libboost-all-dev -y
RUN apt-get install libmysqlcppconn-dev -y

# Install CUDA development tools
RUN apt-get update && apt-get install -y \
    cuda-toolkit-11-6 \
    && apt-get clean

# Install any Python dependencies (optional, if using Python for data processing)
RUN pip3 install --no-cache-dir numpy pandas

# Copy your project files into the container
COPY . /workspace

# Set the environment variables for CUDA
ENV PATH=/usr/local/cuda-11.6/bin${PATH:+:${PATH}}
ENV LD_LIBRARY_PATH=/usr/local/cuda-11.6/lib64/stubs:${LD_LIBRARY_PATH}
ENV CUDA_HOME=/usr/local/cuda-11.6

# Expose ports if needed for communication with other services
EXPOSE 8080

# Default command to keep the container running
CMD ["sleep", "infinity"]
