# MicroPython USB488 module
#
# Test and Measurement Class
#
# MIT license; Copyright (c) 2025 Kazuki Yamamoto

from micropython import const
import time
import usb.device
from usb.device.core import Interface, Descriptor, split_bmRequestType, Buffer
from tmc import TMCInterface

_PROTOCOL_488 = const(0x01)


class Usb488Interface(TMCInterface):
    def __init__(self):
        super().__init__(
            protocol=_PROTOCOL_488,
            interface_str="MicroPython USB488 device",
        )
