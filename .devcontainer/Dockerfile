# Usa imagem base do Ubuntu 24.04
FROM mcr.microsoft.com/devcontainers/base:ubuntu-24.04

# Evita prompts do Debian/Ubuntu
ENV DEBIAN_FRONTEND=noninteractive

# Instala pacotes essenciais
RUN apt-get update && apt-get install -y --no-install-recommends \
    cmake \
    build-essential \
    wget \
    gnupg \
    ca-certificates \
    software-properties-common \
    gcc-mingw-w64-x86-64 \
    ninja-build \
    git \
    python3 \
    python3-pip \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Instala o repositório da NVIDIA para CUDA
RUN wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2404/x86_64/cuda-keyring_1.1-1_all.deb && \
    dpkg -i cuda-keyring_1.1-1_all.deb && \
    rm cuda-keyring_1.1-1_all.deb

# Instala o CUDA Toolkit 12.9
RUN apt-get update && \
    apt-get install -y --no-install-recommends cuda-toolkit-12-9 && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Define variáveis de ambiente para o CUDA
ENV PATH=/usr/local/cuda-12.9/bin:${PATH}
ENV LD_LIBRARY_PATH=/usr/local/cuda-12.9/lib64:${LD_LIBRARY_PATH}
