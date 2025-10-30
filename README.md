# pipico-micropython-scpi

Experimental repo for an SCPI device emulation using **Raspberry Pi Pico** + **micropython**

## Easy use

1. Get the latest micropython UF2 firmware from official: <https://micropython.org/download/RPI_PICO/>
2. Install the firmware into Pico
3. Copy `main.py`, `MicroScpiDevice.py` and `RaspberryScpiPico.py` files into the root of the target device
4. Restart device and pico is ready for use

## Build firmware by yourself

1. Clone the repository
2. Run `make docker` to build a Docker image
3. Run `make firmware` to build the UF2 firmware, which appears in `build` directory

# Documentation

[
`c103` tag](https://github.com/K4zuki/pipico-micropython-scpi/releases/tag/c103) is old but stable version with API document PDF prepared.
