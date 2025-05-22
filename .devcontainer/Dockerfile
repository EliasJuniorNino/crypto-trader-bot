# Use a imagem base do devcontainer para Ubuntu Jammy
FROM mcr.microsoft.com/devcontainers/base:jammy

# Instala gcc-mingw-w64-x86-64 e limpa cache do apt para manter a imagem leve
RUN apt-get update && \
    apt-get install -y gcc-mingw-w64-x86-64 && \
    apt-get clean && rm -rf /var/lib/apt/lists/*
