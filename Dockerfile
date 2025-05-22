FROM nvidia/cuda:12.9.0-cudnn-devel-ubuntu24.04

WORKDIR /workspaces

ARG DEBIAN_FRONTEND=noninteractive

ENV GO_VERSION=1.22.3

RUN apt-get update && apt-get install -y \
  python3 \
  python3-pip \
  python3-venv \
  curl \
  git \
  build-essential \
  gcc-mingw-w64-x86-64 \
  openssh-client \
  sudo \
  wget \
  vim \
  ca-certificates \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

# Instalar Go
RUN wget https://go.dev/dl/go${GO_VERSION}.linux-amd64.tar.gz && \
  tar -C /usr/local -xzf go${GO_VERSION}.linux-amd64.tar.gz && \
  rm go${GO_VERSION}.linux-amd64.tar.gz

# Configurar PATH do Go
ENV PATH="/usr/local/go/bin:${PATH}"

# Copiar requirements.txt para dentro do container
COPY /python-project/requirements.txt /python-project/requirements.txt

# criar diretorio venv
RUN python3 -m venv /python-project/venv

# Ativar o venv
RUN . /python-project/venv/bin/activate

# Instalar pacotes do requirements.txt
RUN /python-project/venv/bin/python3 -m pip install --upgrade pip
RUN /python-project/venv/bin/python3 -m pip install -r requirements.txt

WORKDIR /workspaces/app

CMD ["bash"]
