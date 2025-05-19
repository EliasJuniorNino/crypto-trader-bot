FROM nvidia/cuda:12.9.0-cudnn-devel-ubuntu24.04

WORKDIR /workspaces

ARG DEBIAN_FRONTEND=noninteractive

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

# Copiar requirements.txt para dentro do container
COPY requirements.txt .

# criar diretorio venv
RUN python3 -m venv /venv

# Ativar o venv
RUN . /venv/bin/activate

# Instalar pacotes do requirements.txt
RUN /venv/bin/python3 -m pip install --upgrade pip
RUN /venv/bin/python3 -m pip install -r requirements.txt

WORKDIR /workspaces/CryptoTrader

CMD ["bash"]
