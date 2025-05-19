FROM nvidia/cuda:12.9.0-cudnn-devel-ubuntu24.04

# Set working directory
WORKDIR /workspaces

# Avoid prompts during package installation
ARG DEBIAN_FRONTEND=noninteractive

# Update and install required packages
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    curl \
    git \
    build-essential \
    openssh-client \
    sudo \
    wget \
    vim \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && apt-get clean

# Create a Python virtual environment
ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Upgrade pip inside the virtual environment
RUN pip install --upgrade pip

# Adiciona o usuário vscode (esperado pelo Dev Containers)
ARG USERNAME=vscode
ARG USER_UID=1000
ARG USER_GID=$USER_UID

RUN groupadd --gid $USER_GID $USERNAME \
    && useradd --uid $USER_UID --gid $USER_GID -m $USERNAME \
    && echo "$USERNAME ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers.d/$USERNAME \
    && chmod 0440 /etc/sudoers.d/$USERNAME

# Set PATH so that the virtualenv is accessible to the non-root user
RUN echo "PATH=$VIRTUAL_ENV/bin:$PATH" >> /home/$USERNAME/.bashrc

# Verify installations
RUN echo "Python version:" && python --version \
    && echo "Node.js version:" && node --version \
    && echo "npm version:" && npm --version \
    && echo "CUDA version:" && nvcc --version

USER $USERNAME