#!/usr/bin/env bash

MANIFEST=/root/manifest.py
make -C ports/rp2 -j6 BOARD=RPI_PICO FROZEN_MANIFEST=$MANIFEST clean
make -C ports/rp2 -j6 BOARD=RPI_PICO FROZEN_MANIFEST=$MANIFEST clean all
mv /raspberrypi-pico/micropython/ports/rp2/build-RPI_PICO/firmware.uf2 /root/pipico-micropython-scpi.uf2
