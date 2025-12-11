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

"""
4.2.2 GET_CAPABILITIES
When a device receives this request, the device must queue the response shown below in Table 8.
Table 8 -- GET_CAPABILITIES response packet
-----------------------------------------------------------------------------------------------------------------------------------------------------------------------
|Offset         |Field                          |Size       |Value      |Description
-----------------------------------------------------------------------------------------------------------------------------------------------------------------------
|0-11           |Reserved                       |12         |Reserved   |See the USBTMC specification, Table 37. 488.2 USB488 interfaces
|               |                               |           |           |must set USBTMCInterfaceCapabilities.D1 = 0 and
|               |                               |           |           |USBTMCInterfaceCapabilities.D0 = 0.
|12             |bcdUSB488                      |2          |BCD        |BCD version number of the relevant USB488 specification for this
|               |                               |           |(0x0100 or |USB488 interface. Format is as specified for bcdUSB in the USB 2.0
|               |                               |           |greater)   |specification, section 9.6.1.
|14             |USB488InterfaceCapabilities    |1          |Bitmap     |D7...D3    |Reserved. All bits must be 0.
|               |                               |           |           |D2         |1 – The interface is a 488.2 USB488 interface.
|               |                               |           |           |           |0 – The interface is not a 488.2 USB488 interface.
|               |                               |           |           |D1         |1 – The interface accepts REN_CONTROL,
|               |                               |           |           |           |       GO_TO_LOCAL, and LOCAL_LOCKOUT requests.
|               |                               |           |           |           |0 – The interface does not accept REN_CONTROL,
|               |                               |           |           |           |       GO_TO_LOCAL, and LOCAL_LOCKOUT requests.
|               |                               |           |           |           |       The device, when REN_CONTROL,
|               |                               |           |           |           |       GO_TO_LOCAL, and LOCAL_LOCKOUT requests
|               |                               |           |           |           |       are received, must treat these commands as a nondefined
|               |                               |           |           |           |       command and return a STALL handshake
|               |                               |           |           |           |       packet.
|               |                               |           |           |D0         |1 – The interface accepts the MsgID = TRIGGER
|               |                               |           |           |           |       USBTMC command message and forwards
|               |                               |           |           |           |       TRIGGER requests to the Function Layer.
|               |                               |           |           |           |0 – The interface does not accept the TRIGGER
|               |                               |           |           |           |       USBTMC command message. The device, when the
|               |                               |           |           |           |       TRIGGER USBTMC command message is receives
|               |                               |           |           |           |       must treat it as an unknown MsgID and halt the
|               |                               |           |           |           |       Bulk-OUT endpoint.
|15             |USB488DeviceCapabilities       |1          |Bitmap     |D7...D4    |Reserved. All bits must be 0.         
|               |                               |           |           |D3         |1 – The device understands all mandatory SCPI
|               |                               |           |           |           |   commands. See SCPI Chapter 4, SCPI Compliance
|               |                               |           |           |           |   Criteria.
|               |                               |           |           |           |0 – The device may not understand all mandatory SCPI
|               |                               |           |           |           |   commands. If the parser is dynamic and may not
|               |                               |           |           |           |   understand SCPI, this bit must = 0.
|               |                               |           |           |D2         |1 – The device is SR1 capable. The interface must have
|               |                               |           |           |           |   an Interrupt-IN endpoint. The device must use the
|               |                               |           |           |           |   Interrupt-IN endpoint as described in 3.4.1 to
|               |                               |           |           |           |   request service, in addition to the other uses
|               |                               |           |           |           |   described in this specification.
|               |                               |           |           |           |0 – The device is SR0. If the interface contains an
|               |                               |           |           |           |   Interrupt-IN endpoint, the device must not use the
|               |                               |           |           |           |   Interrupt-IN endpoint as described in 3.4.1 to
|               |                               |           |           |           |   request service. The device must use the endpoint
|               |                               |           |           |           |   for all other uses described in this specification.
|               |                               |           |           |           |   See IEEE 488.1, section 2.7. If USB488Interface
|               |                               |           |           |           |   Capabilities.D2 = 1, also see IEEE 488.2, section 5.5.
|               |                               |           |           |D1         |1 – The device is RL1 capable. The device must
|               |                               |           |           |           |   implement the state machine shown in Figure 2.
|               |                               |           |           |           |0 – The device is RL0. The device does not implement
|               |                               |           |           |           |   the state machine shown in Figure 2.
|               |                               |           |           |           |   See IEEE 488.1, section 2.8. If USB488Interface
|               |                               |           |           |           |   Capabilities.D2 = 1, also see IEEE 488.2, section 5.6.
|               |                               |           |           |D0         |1 – The device is DT1 capable.
|               |                               |           |           |           |0 – The device is DT0.
|               |                               |           |           |           |   See IEEE 488.1, section 2.11. If USB488Interface
|               |                               |           |           |           |   Capabilities.D2 = 1, also see IEEE 488.2, section 5.9.
|16             |Reserved                       |8          |All bytes  |Reserved for USB488 use. All bytes must be 0x00.
|               |                               |           |must be    |
|               |                               |           |0x00.      |
-----------------------------------------------------------------------------------------------------------------------------------------------------------------------
The following rules must be followed:
1. If USB488DeviceCapabilities.D0 = 1 (DT1) then USB488InterfaceCapabilities.D0 must = 1.
2. If USB488DeviceCapabilities.D1 = 1 (RL1) then USB488InterfaceCapabilities.D1 must = 1.
3. If USB488InterfaceCapabilities.D2 = 1 (488.2 USB488 interface) then USB488DeviceCapabilities.D2 must = 1 (SR1).
4. If USB488DeviceCapabilities.D3 = 1 (SCPI) then USB488DeviceCapabilities.D2 must = 1 (SR1) and USB488InterfaceCapabilities.D2 must = 1 (488.2 USB488 interface).
"""
_bcdUSB488 = const(0x0100)

"""
3.2.1 USB488 defined Bulk-OUT command messages
The USBTMC specification reserves a range of MsgID values for USBTMC subclasses to define. Table 1
below shows the MsgID definitions for the USB488 subclass.

Table 1 -- USB488 defined MsgID values
------------------------------------------------------------------------------------------------------------------------
|MsgID      |Direction          |MACRO                  |Description
|           |OUT=Host-to-device |                       |
|           |IN=Device-to-Host  |                       |
------------------------------------------------------------------------------------------------------------------------
|128        |OUT                |TRIGGER                |The TRIGGER command message provides a
|           |                   |                       |mechanism for the Host to trigger device dependent
|           |                   |                       |actions on a device synchronously with other Bulk-OUT
|           |                   |                       |messages. Support for this MsgID is optional. See 4.2.2.
|           |IN                 |(no defined response)  |There is no defined response for this command.
|129-191    |Reserved           |Reserved               |Reserved for USBTMC subclass use.
------------------------------------------------------------------------------------------------------------------------
"""
_MSGID_DEV_DEP_MSG_OUT = const(1)
_MSGID_TRIGGER = const(128)


class Usb488Interface(TMCInterface):
    def __init__(self):
        super().__init__(
            protocol=_PROTOCOL_488,
            interface_str="MicroPython USB488 device",
            interrupt_ep=True
        )

    def get_capabilities(self):
        usb488_dev_capabilities = 1 << 3 | 1 << 2  # SCPI, SR1, RL0, DT0
        usb488_itf_capabilities = 1 << 2 | 0 << 1 | 0  # USB488, not accept REN_CONTROL, GO_TO_LOCAL, LOCAL_LOCKOUT, TRIGGER

        resp = super().get_capabilities()
        resp.pack_into("H", 12, _bcdUSB488)
        resp.pack_into("B", 14, usb488_itf_capabilities)
        resp.pack_into("B", 15, usb488_dev_capabilities)

        return resp.b
