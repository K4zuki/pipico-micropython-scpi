#!/usr/bin/env bash

MANIFEST=/root/cdc/manifest.py
make -C ports/rp2 -j6 BOARD=RPI_PICO FROZEN_MANIFEST=$MANIFEST clean
make -C ports/rp2 -j6 BOARD=RPI_PICO FROZEN_MANIFEST=$MANIFEST clean all
mkdir -p /root/build
mv /raspberrypi-pico/micropython/ports/rp2/build-RPI_PICO/firmware.uf2 /root/build/pipico-micropython-scpi-cdc.uf2
echo $(REF)
