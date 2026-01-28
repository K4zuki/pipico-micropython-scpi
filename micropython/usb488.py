# MicroPython USB488 module
#
# Test and Measurement Class
#
# MIT license; Copyright (c) 2025 Kazuki Yamamoto

from micropython import const
import time
import struct
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
            indicator_pulse=True,
            interrupt_ep=True
        )

    def get_capabilities(self):
        usb488_dev_capabilities = 1 << 3 | 1 << 2  # SCPI, SR1, RL0, DT0
        usb488_itf_capabilities = 1 << 2 | 0 << 1 | 0  # USB488, not accept REN_CONTROL, GO_TO_LOCAL, LOCAL_LOCKOUT, TRIGGER

        resp = Descriptor(super().get_capabilities())
        resp.pack_into("H", 12, _bcdUSB488)
        resp.pack_into("B", 14, usb488_itf_capabilities)  # USB488InterfaceCapabilities
        resp.pack_into("B", 15, usb488_dev_capabilities)  # USB488DeviceCapabilities

        return resp.b

    def on_device_dependent_out(self) -> None:
        """ Action on Bulk out transfer with megID==DEV_DEP_MSG_OUT.
        Subclasses must override this method.

        :param b_tag:
        :param tmc_specific:
        :param message:
        :return:
        """
        """ Table 3 -- Example *IDN? Bulk-OUT USBTMC device dependent command message
                    |Offset |Field                      |Size   |Value                  |Description
        ------------------------------------------------------------------------------------------------------------------------
        Bulk-OUT    |0      |MsgID                      |1      |DEV_DEP_MSG_OUT        |See the USBTMC specification,
        Header      |1      |bTag                       |1      |0x01 (varies with each |Table 1.
                    |       |                           |       |transfer)              |
                    |2      |bTagInverse                |1      |0xFE                   |
                    |3      |Reserved                   |1      |0x00                   |
        ------------------------------------------------------------------------------------------------------------------------
        USBTMC      |4      |TransferSize               |4      |0x06                   |Command specific content.
        device      |5      |                           |       |0x00                   |See the USBTMC specification,
        dependent   |6      |                           |       |0x00                   |Table 3.
        command     |7      |                           |       |0x00                   |
        message     |8      |bmTransfer                 |1      |0x01 (EOM is set).     |
                    |       |Attributes                 |       |                       |
                    |9      |Reserved                   |1      |0x00                   |
                    |10     |Reserved                   |1      |0x00                   |
                    |11     |Reserved                   |1      |0x00                   |
                    |12     |Device dependent           |1      |0x2A = ‘*’             |USBTMC message data byte 0.
                    |13     |message data bytes         |1      |0x49 = ‘I’             |USBTMC message data byte 1.
                    |14     |                           |1      |0x44 = ‘D’             |USBTMC message data byte 2.
                    |15     |                           |1      |0x4E = ‘N’             |USBTMC message data byte 3.
                    |16     |                           |1      |0x3F = ‘?’             |USBTMC message data byte 4.
                    |17     |                           |1      |0x0A = ‘\n’ = newline  |USBTMC message data byte 5.
        ------------------------------------------------------------------------------------------------------------------------
                    |18-19  |Alignment bytes            |2      |0x0000                 |Two alignment bytes are added
                    |       |(required to make the      |       |(not required to be    |to bring the number of DATA
                    |       |number of bytes in the     |       |0x0000)                |bytes in the transaction to 20,
                    |       |transaction a multiple of  |       |                       |which is divisible by 4.
                    |       |4)                         |       |                       |

        """
        transfer_size, attribute = struct.unpack_from("<IB3x", self.last_bulkout_msg.tmc_specific, 0)
        print("Transfer size:", transfer_size)
        print("Attribute:", attribute)
        message = self.last_bulkout_msg.message
        print("Message:", bytes(message))
        p = len(message)
        print("Actual message size:", p)

    def on_request_device_dependent_in(self) -> None:
        """ Action on Bulk out transfer with megID==DEV_DEP_MSG_IN.
        Subclasses must override this method.

        :param b_tag:
        :param tmc_specific:
        :param message:
        """
        """ Table 4 -- REQUEST_DEV_DEP_MSG_IN Bulk-OUT Header with command specific content
                    |Offset |Field          |Size   |Value          |Description
        ------------------------------------------------------------------------------------------------------------------------
                    |0-3    |See Table 1.   |4      |See Table 1.   |See Table 1.
        ------------------------------------------------------------------------------------------------------------------------
        USBTMC      |4-7    |TransferSize   |4      |Number         |Total number of USBTMC message data bytes to be
        command     |       |               |       |               |sent in this USB transfer. This does not include the
        specific    |       |               |       |               |number of bytes in this Bulk-OUT Header or
        content     |       |               |       |               |alignment bytes. Sent least significant byte first,
                    |       |               |       |               |most significant byte last. TransferSize must be >
                    |       |               |       |               |0x00000000.
                    |8      |bmTransfer     |1      |Bitmap         |D7...D2    |Reserved. All bits must be 0.
                    |       |Attributes     |       |               |D1         |TermCharEnabled.
                    |       |               |       |               |           |1 – The Bulk-IN transfer must terminate
                    |       |               |       |               |           |   on the specified TermChar. The Host
                    |       |               |       |               |           |   may only set this bit if the USBTMC
                    |       |               |       |               |           |   interface indicates it supports
                    |       |               |       |               |           |   TermChar in the GET_CAPABILITIES
                    |       |               |       |               |           |   response packet.
                    |       |               |       |               |           |0 – The device must ignore TermChar.
                    |       |               |       |               |D0         |Must be 0.
                    |9      |TermChar       |1      |Value          |If bmTransferAttributes.D1 = 1, TermChar is an 8-bit
                    |       |               |       |               |value representing a termination character. If
                    |       |               |       |               |supported, the device must terminate the Bulk-IN
                    |       |               |       |               |transfer after this character is sent.
                    |       |               |       |               |If bmTransferAttributes.D1 = 0, the device must ignore
                    |       |               |       |               |this field.
                    |10-11  |Reserved       |2      |0x0000         |Reserved. Must be 0x0000.
        """
        transfer_size, attribute, termchar = struct.unpack_from("<IBB2x", self.last_bulkout_msg.tmc_specific, 0)
        print("on_request_device_dependent_in")

        header: Descriptor = self.draft_device_dependent_in_header(self.last_bulkout_msg.b_tag, transfer_size)
        if len(self.dev_dep_out_messages) > 0:
            message = self.dev_dep_out_messages.popleft()
            print("response message:", message)
            self.send_device_dependent_in(header, message)
        else:
            print("No response stack left")
