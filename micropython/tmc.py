# MicroPython USB tmc module
#
# Test and Measurement Class
#
# MIT license; Copyright (c) 2025 Kazuki Yamamoto

from micropython import const
import machine
import struct
import time

from usb.device.core import Interface, Descriptor, split_bmRequestType, Buffer

_EP_IN_FLAG = const(1 << 7)

_INTERFACE_CLASS_TMC = const(0xFE)
_INTERFACE_SUBCLASS_TMC = const(0x03)

_PROTOCOL_NONE = const(0x00)
_PROTOCOL_488 = const(0x01)


class TMCInterface(Interface):
    def __init__(self, **kwargs):
        super().__init__()
        self.ep_out = None  # Set during enumeration. RX direction (host to device)
        self.ep_in = None  # TX direction (device to host)
        self._rx = Buffer(64)
        self._tx = Buffer(64)

    def desc_cfg(self, desc, itf_num, ep_num, strs):
        # Function to build configuration descriptor contents for this interface
        # or group of interfaces. This is called on each interface from
        # USBDevice.init().
        #
        # This function should insert:
        #
        # - At least one standard Interface descriptor (can call
        # - desc.interface()).
        desc.interface(itf_num, 0, _INTERFACE_CLASS_TMC, _INTERFACE_SUBCLASS_TMC, _PROTOCOL_488)

        # Plus, optionally:
        #
        # - One or more endpoint descriptors (can call desc.endpoint()).
        # - An Interface Association Descriptor, prepended before.
        # - Other class-specific configuration descriptor data.
        #
        # This function is called twice per call to USBDevice.init(). The first
        # time the values of all arguments are dummies that are used only to
        # calculate the total length of the descriptor. Therefore, anything this
        # function does should be idempotent and it should add the same
        # descriptors each time. If saving interface numbers or endpoint numbers
        # for later
        #
        # Parameters:
        #
        # - desc - Descriptor helper to write the configuration descriptor bytes into.
        #   The first time this function is called 'desc' is a dummy object
        #   with no backing buffer (exists to count the number of bytes needed).
        #
        # - itf_num - First bNumInterfaces value to assign. The descriptor
        #   should contain the same number of interfaces returned by num_itfs(),
        #   starting from this value.
        #
        # - ep_num - Address of the first available endpoint number to use for
        #   endpoint descriptor addresses. Subclasses should save the
        #   endpoint addresses selected, to look up later (although note the first
        #   time this function is called, the values will be dummies.)
        #
        # - strs - list of string descriptors for this USB device. This function
        #   can append to this list, and then insert the index of the new string
        #   in the list into the configuration descriptor.

    def num_eps(self):
        # Return the number of USB Endpoint numbers represented by this object
        # (as set in desc_cfg().)
        #
        # Note for each count returned by this function, the interface may
        # choose to have both an IN and OUT endpoint (i.e. IN flag is not
        # considered a value here.)
        #
        # This value can be zero, if the USB Host only communicates with this
        # interface using control transfers.
        return 2  # 1x Bulk + 1x Interrupt
