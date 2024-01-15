FROM ubuntu

RUN apt-get update && apt upgrade -y && \
    apt-get install -y --no-install-recommends \
        cmake \
        build-essential \
        binutils-arm-none-eabi \
        gcc-arm-none-eabi \
        libnewlib-dev \
        libstdc++-arm-none-eabi-newlib \
        git \
        ca-certificates \
        python3 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /raspberrypi-pico

RUN git clone https://github.com/micropython/micropython.git -b v1.22.1

WORKDIR /raspberrypi-pico/micropython/
RUN make -j4 -C mpy-cross
RUN make -C ports/rp2 -j4 BOARD=RPI_PICO submodules

#RUN make -C ports/rp2 -j4 BOARD=RPI_PICO FROZEN_MANIFEST=$MANIFEST
